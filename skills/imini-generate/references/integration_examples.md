# Integration code templates

Templates for the complete async flow: **submit → poll → extract result**. Each one is copy-paste runnable; adapt the body payload using the chosen model's OpenAPI YAML.

Every template handles:

- **Status enum** — `queued` / `processing` / `succeeded` / `failed` (the only four values returned; never check for `completed` / `running` / `pending`)
- **Result iteration** — `images[]` / `videos[]` arrays; **always iterate, never index `[0]`** (calls with `n` / `num_images` return multiple outputs; some video models return multiple segments)
- **Jitter** — ±20% on every interval, to avoid thundering-herd retries
- **HTTP 429** — backoff floor bumped to ≥5s before next attempt
- **Structured error preservation** — `error.code` / `error.message` / `error.request_id` surfaced on failures so callers can log `request_id` for imini support

Common constants:

- Base URL: `https://openapi.imini.ai/imini/router`
- Submit: `POST /v1/images/generate` or `POST /v1/videos/generate`
- Query: `GET /v1/images/tasks/{task_id}` or `GET /v1/videos/tasks/{task_id}`
- Auth header: `Authorization: Bearer ${IMINI_API_KEY}`

---

## Python (sync, stdlib only — no pip install needed)

```python
import json
import os
import random
import time
import urllib.error
import urllib.request

BASE_URL = "https://openapi.imini.ai/imini/router"
API_KEY = os.environ["IMINI_API_KEY"]


class IminiHTTPError(RuntimeError):
    def __init__(self, status: int, body: str, request_id: str | None = None):
        self.status = status
        self.body = body
        self.request_id = request_id
        super().__init__(f"HTTP {status}: {body}")


def _request(method: str, path: str, body: dict | None = None) -> dict:
    req = urllib.request.Request(
        BASE_URL + path,
        data=json.dumps(body).encode("utf-8") if body is not None else None,
        method=method,
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace")
        req_id = None
        try:
            req_id = json.loads(raw).get("error", {}).get("request_id")
        except Exception:
            pass
        raise IminiHTTPError(e.code, raw, req_id) from e


def _jittered(interval: float) -> float:
    return interval * (0.8 + 0.4 * random.random())


def submit_image(prompt: str, model: str = "google/nano-banana-pro", **extra) -> dict:
    return _request("POST", "/v1/images/generate", {"model": model, "prompt": prompt, **extra})


def poll_image(task_id: str, start: float = 2.0, cap: float = 30.0, timeout: float = 600.0) -> dict:
    """Default timeout 600s (10 min). See references/errors.md."""
    deadline = time.monotonic() + timeout
    interval = start
    while time.monotonic() < deadline:
        try:
            result = _request("GET", f"/v1/images/tasks/{task_id}")
        except IminiHTTPError as e:
            if e.status == 429:
                interval = max(interval, 5.0)
            elif e.status >= 500:
                pass  # transient — retry after backoff
            else:
                raise  # 4xx other than 429 — caller must surface
        else:
            status = result.get("status")
            if status == "succeeded":
                return result
            if status == "failed":
                raise RuntimeError(f"Task failed: {result.get('error')}")
        time.sleep(_jittered(interval))
        interval = min(interval * 1.5, cap)
    raise TimeoutError(f"Task {task_id} did not complete within {timeout}s")


if __name__ == "__main__":
    task = submit_image(
        prompt="A cute shiba inu in a spacesuit on the moon, 3D cartoon",
        resolution="4K",
        aspect_ratio="16:9",
    )
    result = poll_image(task["task_id"])
    # ALWAYS iterate — calls may return multiple images via n / num_images
    for i, img in enumerate(result["images"]):
        print(f"[{i}] {img['url']}  ({img['width']}x{img['height']})")
    print(f"task_id={task['task_id']} request_id={result.get('request_id')}")
```

Swap `images` → `videos` in paths and bump the default timeout to 1800s (30 min) for video models.

---

## Python (async, requires `aiohttp`)

```bash
pip install aiohttp>=3.9
```

```python
import asyncio
import os
import random

import aiohttp

BASE_URL = "https://openapi.imini.ai/imini/router"
API_KEY = os.environ["IMINI_API_KEY"]


class IminiHTTPError(RuntimeError):
    def __init__(self, status: int, body: str, request_id: str | None = None):
        self.status = status
        self.body = body
        self.request_id = request_id
        super().__init__(f"HTTP {status}: {body}")


def _jittered(interval: float) -> float:
    return interval * (0.8 + 0.4 * random.random())


async def _request(session: aiohttp.ClientSession, method: str, path: str, body: dict | None = None) -> dict:
    async with session.request(method, BASE_URL + path, json=body) as resp:
        text = await resp.text()
        if resp.status >= 400:
            req_id = None
            try:
                import json
                req_id = json.loads(text).get("error", {}).get("request_id")
            except Exception:
                pass
            raise IminiHTTPError(resp.status, text, req_id)
        import json
        return json.loads(text)


async def submit(session, path: str, payload: dict) -> dict:
    return await _request(session, "POST", path, payload)


async def poll(session, query_path: str, task_id: str, start: float = 2.0, cap: float = 30.0, timeout: float = 900.0) -> dict:
    loop = asyncio.get_running_loop()
    deadline = loop.time() + timeout
    interval = start
    while loop.time() < deadline:
        try:
            result = await _request(session, "GET", f"{query_path}/{task_id}")
        except IminiHTTPError as e:
            if e.status == 429:
                interval = max(interval, 5.0)
            elif e.status >= 500:
                pass
            else:
                raise
        else:
            status = result.get("status")
            if status == "succeeded":
                return result
            if status == "failed":
                raise RuntimeError(f"Task failed: {result.get('error')}")
        await asyncio.sleep(_jittered(interval))
        interval = min(interval * 1.5, cap)
    raise TimeoutError(f"Task {task_id} did not complete within {timeout}s")


async def generate_batch(prompts: list[str], concurrency: int = 10) -> list[dict]:
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }
    sem = asyncio.Semaphore(concurrency)

    async with aiohttp.ClientSession(headers=headers) as session:
        async def one(prompt: str) -> dict:
            async with sem:
                task = await submit(
                    session,
                    "/v1/images/generate",
                    {"model": "google/nano-banana-2", "prompt": prompt, "resolution": "1K"},
                )
                return await poll(session, "/v1/images/tasks", task["task_id"])

        return await asyncio.gather(*(one(p) for p in prompts))


if __name__ == "__main__":
    prompts = [f"Portrait of a cat wearing a hat, variation {i}" for i in range(100)]
    results = asyncio.run(generate_batch(prompts, concurrency=10))
    for r in results:
        for img in r["images"]:  # ALWAYS iterate
            print(img["url"])
    print(f"Generated {sum(len(r['images']) for r in results)} images")
```

---

## Node.js (requires **Node 18+** for native `fetch`)

> If you must support Node <18, install `node-fetch` and `import fetch from 'node-fetch'`. Native fetch is preferred — fewer dependencies.

```javascript
// imini-client.mjs — run with: node imini-client.mjs
const BASE_URL = "https://openapi.imini.ai/imini/router";
const API_KEY = process.env.IMINI_API_KEY;
if (!API_KEY) throw new Error("IMINI_API_KEY is required");

class IminiHTTPError extends Error {
    constructor(status, body, requestId) {
        super(`HTTP ${status}: ${body}`);
        this.status = status;
        this.body = body;
        this.requestId = requestId;
    }
}

const jittered = (interval) => interval * (0.8 + 0.4 * Math.random());
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

async function request(method, path, body) {
    const resp = await fetch(BASE_URL + path, {
        method,
        headers: {
            Authorization: `Bearer ${API_KEY}`,
            "Content-Type": "application/json",
        },
        body: body ? JSON.stringify(body) : undefined,
    });
    const text = await resp.text();
    if (!resp.ok) {
        let requestId;
        try { requestId = JSON.parse(text)?.error?.request_id; } catch {}
        throw new IminiHTTPError(resp.status, text, requestId);
    }
    return JSON.parse(text);
}

async function submitVideo(payload) {
    return request("POST", "/v1/videos/generate", payload);
}

async function pollVideo(taskId, { startMs = 5000, capMs = 30000, timeoutMs = 1800000 } = {}) {
    // timeoutMs default 1.8M = 30min — see references/errors.md for per-scenario tuning.
    const deadline = Date.now() + timeoutMs;
    let interval = startMs;
    while (Date.now() < deadline) {
        try {
            const result = await request("GET", `/v1/videos/tasks/${taskId}`);
            if (result.status === "succeeded") return result;
            if (result.status === "failed") {
                throw new Error(`Task failed: ${JSON.stringify(result.error)}`);
            }
        } catch (e) {
            if (e instanceof IminiHTTPError) {
                if (e.status === 429) interval = Math.max(interval, 5000);
                else if (e.status >= 500) { /* transient — retry */ }
                else throw e;
            } else {
                throw e;
            }
        }
        await sleep(jittered(interval));
        interval = Math.min(interval * 1.5, capMs);
    }
    throw new Error(`Task ${taskId} timed out after ${timeoutMs}ms`);
}

(async () => {
    const task = await submitVideo({
        model: "kling/kling-v3-omni",
        prompt: "A drone shot over a snowy mountain range at sunrise",
        resolution: "1080P",
        duration: 5,
    });
    const result = await pollVideo(task.task_id);
    // ALWAYS iterate — some models / params produce multiple segments
    for (const v of result.videos ?? []) {
        console.log(`${v.url}  ${v.width}x${v.height}  ${v.duration}s`);
    }
})();
```

---

## TypeScript (requires **Node 18+** for native `fetch`)

```typescript
// imini-client.ts
const BASE_URL = "https://openapi.imini.ai/imini/router";
const API_KEY = process.env.IMINI_API_KEY!;
if (!API_KEY) throw new Error("IMINI_API_KEY is required");

export type TaskStatus = "queued" | "processing" | "succeeded" | "failed";

export interface IminiError {
    code: string;
    message: string;
    status: number;
    request_id: string;
}

export interface ImageOutput { url: string; width: number; height: number; }
export interface VideoOutput { url: string; width: number; height: number; duration: number; }

export interface ImageTask {
    task_id: string;
    status: TaskStatus;
    images?: ImageOutput[];
    error?: IminiError;
    request_id?: string;
}

export interface VideoTask {
    task_id: string;
    status: TaskStatus;
    videos?: VideoOutput[];
    error?: IminiError;
    request_id?: string;
}

export class IminiHTTPError extends Error {
    constructor(public status: number, public body: string, public requestId?: string) {
        super(`HTTP ${status}: ${body}`);
    }
}

const jittered = (n: number) => n * (0.8 + 0.4 * Math.random());
const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

async function request<T>(method: "GET" | "POST", path: string, body?: unknown): Promise<T> {
    const resp = await fetch(BASE_URL + path, {
        method,
        headers: {
            Authorization: `Bearer ${API_KEY}`,
            "Content-Type": "application/json",
        },
        body: body ? JSON.stringify(body) : undefined,
    });
    const text = await resp.text();
    if (!resp.ok) {
        let requestId: string | undefined;
        try { requestId = JSON.parse(text)?.error?.request_id; } catch {}
        throw new IminiHTTPError(resp.status, text, requestId);
    }
    return JSON.parse(text) as T;
}

export async function generateImage(payload: Record<string, unknown>): Promise<ImageTask> {
    const submitted = await request<ImageTask>("POST", "/v1/images/generate", payload);
    return pollTask<ImageTask>(submitted.task_id, "/v1/images/tasks");
}

export async function generateVideo(payload: Record<string, unknown>): Promise<VideoTask> {
    const submitted = await request<VideoTask>("POST", "/v1/videos/generate", payload);
    // Videos: bump defaults — see references/errors.md
    return pollTask<VideoTask>(submitted.task_id, "/v1/videos/tasks", {
        startMs: 5000,
        timeoutMs: 1_800_000,
    });
}

async function pollTask<T extends { status: TaskStatus; error?: IminiError }>(
    taskId: string,
    basePath: string,
    { startMs = 2000, capMs = 30000, timeoutMs = 900_000 }: { startMs?: number; capMs?: number; timeoutMs?: number } = {},
): Promise<T> {
    const deadline = Date.now() + timeoutMs;
    let interval = startMs;
    while (Date.now() < deadline) {
        try {
            const result = await request<T>("GET", `${basePath}/${taskId}`);
            if (result.status === "succeeded") return result;
            if (result.status === "failed") {
                throw new Error(`Task failed: ${JSON.stringify(result.error)}`);
            }
        } catch (e) {
            if (e instanceof IminiHTTPError) {
                if (e.status === 429) interval = Math.max(interval, 5000);
                else if (e.status >= 500) { /* transient — retry */ }
                else throw e;
            } else {
                throw e;
            }
        }
        await sleep(jittered(interval));
        interval = Math.min(interval * 1.5, capMs);
    }
    throw new Error(`Task ${taskId} timed out after ${timeoutMs}ms`);
}

// Usage:
//   const result = await generateImage({ model: "google/nano-banana-pro", prompt: "...", resolution: "4K" });
//   for (const img of result.images ?? []) console.log(img.url, img.width, img.height);
```

---

## cURL (two-step manual flow)

```bash
#!/usr/bin/env bash
set -euo pipefail

BASE="https://openapi.imini.ai/imini/router"
: "${IMINI_API_KEY:?IMINI_API_KEY is required}"

# 1. Submit
task_json=$(curl -sS -X POST "$BASE/v1/images/generate" \
    -H "Authorization: Bearer $IMINI_API_KEY" \
    -H "Content-Type: application/json" \
    -d '{
        "model": "google/nano-banana-pro",
        "prompt": "A cute shiba inu in a spacesuit on the moon, 3D cartoon",
        "resolution": "4K",
        "aspect_ratio": "16:9"
    }')
echo "Submit: $task_json"

task_id=$(echo "$task_json" | python3 -c 'import sys,json; print(json.load(sys.stdin)["task_id"])')

# 2. Poll — 10 min cap for images (1800 for videos). Iterations: 600s / max-interval(30s) ≈ 20 polls.
interval=2
deadline=$((SECONDS + 600))
while [ "$SECONDS" -lt "$deadline" ]; do
    result=$(curl -sS "$BASE/v1/images/tasks/$task_id" \
        -H "Authorization: Bearer $IMINI_API_KEY")
    status=$(echo "$result" | python3 -c 'import sys,json; print(json.load(sys.stdin).get("status",""))')
    echo "Poll @${SECONDS}s: status=$status"
    case "$status" in
        succeeded)
            # ALWAYS iterate — may be multiple images
            echo "$result" | python3 -c '
import sys, json
r = json.load(sys.stdin)
for i, img in enumerate(r.get("images", [])):
    print(f"[{i}] {img[\"url\"]}  {img[\"width\"]}x{img[\"height\"]}")
'
            exit 0 ;;
        failed) echo "$result" >&2; exit 1 ;;
    esac
    sleep "$interval"
    interval=$((interval * 3 / 2))
    [ "$interval" -gt 30 ] && interval=30
done

echo "Timed out after 600s" >&2
exit 2
```

---

## Notes for code generation

- Always read the API key from `process.env.IMINI_API_KEY` / `os.environ["IMINI_API_KEY"]`. **Never** hard-code keys.
- Keep the submit function and the polling loop as **separate functions** so callers can schedule them independently (e.g. submit many tasks, poll with a worker pool).
- When generating for a specific model, populate `model:` from the chosen model id and map body fields from the OpenAPI YAML's `properties:` list.
- Include inline comments only where the YAML description adds non-obvious constraints (e.g. `prompt up to 6000 chars`).
- For video models with per-second pricing, add a cost-estimate log line after successful completion using `result.videos[i].duration`.
- **Never index `[0]`** on `images` / `videos`. Always iterate the array — even if the caller intends "one output", the API can return more, and silently dropping outputs masks bugs in downstream code.
