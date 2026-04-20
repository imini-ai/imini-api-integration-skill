# Integration code templates

Templates for the complete async flow: **submit → poll → extract result**. Adapt the placeholder fields (`<MODEL_ID>`, `<SUBMIT_PATH>`, `<QUERY_PATH>`, prompt payload) using the chosen model's OpenAPI YAML.

Common constants:

- Base URL: `https://openapi.imini.ai/imini/router`
- Submit: `POST /v1/images/generate` or `POST /v1/videos/generate`
- Query: `GET /v1/images/tasks/{task_id}` or `GET /v1/videos/tasks/{task_id}`
- Auth header: `Authorization: Bearer ${IMINI_API_KEY}`

---

## Python (sync, stdlib only)

```python
import json
import os
import time
import urllib.error
import urllib.request

BASE_URL = "https://openapi.imini.ai/imini/router"
API_KEY = os.environ["IMINI_API_KEY"]


def _request(method, path, body=None):
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
        raise RuntimeError(
            f"{e.code} {e.reason}: {e.read().decode('utf-8', errors='replace')}"
        ) from e


def submit_image(prompt, model="google/nano-banana-pro", **extra):
    payload = {"model": model, "prompt": prompt, **extra}
    return _request("POST", "/v1/images/generate", payload)


def poll_image(task_id, start_interval=2.0, max_interval=30.0, timeout=60.0):
    deadline = time.monotonic() + timeout
    interval = start_interval
    while time.monotonic() < deadline:
        result = _request("GET", f"/v1/images/tasks/{task_id}")
        status = result.get("status")
        if status == "completed":
            return result
        if status == "failed":
            raise RuntimeError(f"Task failed: {result.get('error')}")
        time.sleep(interval)
        interval = min(interval * 1.5, max_interval)
    raise TimeoutError(f"Task {task_id} did not complete within {timeout}s")


if __name__ == "__main__":
    task = submit_image(
        prompt="A cute shiba inu in a spacesuit on the moon, 3D cartoon",
        resolution="4K",
        aspect_ratio="16:9",
    )
    result = poll_image(task["task_id"])
    print(json.dumps(result, indent=2, ensure_ascii=False))
```

Swap `images` → `videos` in paths and scale the timeout (e.g. 600s) for video models.

## Python (async with aiohttp)

```python
import asyncio
import os

import aiohttp

BASE_URL = "https://openapi.imini.ai/imini/router"
API_KEY = os.environ["IMINI_API_KEY"]


async def submit(session, path, payload):
    async with session.post(BASE_URL + path, json=payload) as resp:
        resp.raise_for_status()
        return await resp.json()


async def poll(session, path, task_id, start=2.0, cap=30.0, timeout=60.0):
    loop = asyncio.get_running_loop()
    deadline = loop.time() + timeout
    interval = start
    while loop.time() < deadline:
        async with session.get(f"{BASE_URL}{path}/{task_id}") as resp:
            resp.raise_for_status()
            result = await resp.json()
        if result.get("status") == "completed":
            return result
        if result.get("status") == "failed":
            raise RuntimeError(f"Task failed: {result.get('error')}")
        await asyncio.sleep(interval)
        interval = min(interval * 1.5, cap)
    raise TimeoutError(f"Task {task_id} did not complete within {timeout}s")


async def generate_batch(prompts, concurrency=10):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }
    sem = asyncio.Semaphore(concurrency)

    async with aiohttp.ClientSession(headers=headers) as session:
        async def one(prompt):
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
    print(f"Generated {len(results)} images")
```

## Node.js (native fetch)

```javascript
const BASE_URL = "https://openapi.imini.ai/imini/router";
const API_KEY = process.env.IMINI_API_KEY;

async function request(method, path, body) {
    const resp = await fetch(BASE_URL + path, {
        method,
        headers: {
            Authorization: `Bearer ${API_KEY}`,
            "Content-Type": "application/json",
        },
        body: body ? JSON.stringify(body) : undefined,
    });
    if (!resp.ok) {
        const text = await resp.text();
        throw new Error(`${resp.status} ${resp.statusText}: ${text}`);
    }
    return resp.json();
}

async function submitVideo(payload) {
    return request("POST", "/v1/videos/generate", payload);
}

async function pollVideo(taskId, { startMs = 5000, capMs = 30000, timeoutMs = 600000 } = {}) {
    const deadline = Date.now() + timeoutMs;
    let interval = startMs;
    while (Date.now() < deadline) {
        const result = await request("GET", `/v1/videos/tasks/${taskId}`);
        if (result.status === "completed") return result;
        if (result.status === "failed") {
            throw new Error(`Task failed: ${JSON.stringify(result.error)}`);
        }
        await new Promise((r) => setTimeout(r, interval));
        interval = Math.min(interval * 1.5, capMs);
    }
    throw new Error(`Task ${taskId} timed out`);
}

(async () => {
    const task = await submitVideo({
        model: "kling/kling-v3-omni",
        prompt: "A drone shot over a snowy mountain range at sunrise",
        resolution: "1080P",
        duration: 5,
    });
    const result = await pollVideo(task.task_id);
    console.log(JSON.stringify(result, null, 2));
})();
```

## TypeScript (native fetch)

```typescript
const BASE_URL = "https://openapi.imini.ai/imini/router";
const API_KEY = process.env.IMINI_API_KEY!;

interface SubmitResponse {
    task_id: string;
    model: string;
    created_at: string;
    request_id: string;
}

interface TaskResult<T = unknown> {
    task_id: string;
    status: "pending" | "running" | "completed" | "failed";
    result?: T;
    error?: { code: string; message: string; status: number; request_id: string };
}

async function request<T>(method: "GET" | "POST", path: string, body?: unknown): Promise<T> {
    const resp = await fetch(BASE_URL + path, {
        method,
        headers: {
            Authorization: `Bearer ${API_KEY}`,
            "Content-Type": "application/json",
        },
        body: body ? JSON.stringify(body) : undefined,
    });
    if (!resp.ok) {
        throw new Error(`${resp.status} ${resp.statusText}: ${await resp.text()}`);
    }
    return resp.json() as Promise<T>;
}

export async function generateImage(payload: Record<string, unknown>): Promise<TaskResult> {
    const task = await request<SubmitResponse>("POST", "/v1/images/generate", payload);
    return pollTask<TaskResult>(task.task_id, "/v1/images/tasks");
}

async function pollTask<T extends TaskResult>(
    taskId: string,
    basePath: string,
    { startMs = 2000, capMs = 30000, timeoutMs = 60000 } = {},
): Promise<T> {
    const deadline = Date.now() + timeoutMs;
    let interval = startMs;
    while (Date.now() < deadline) {
        const result = await request<T>("GET", `${basePath}/${taskId}`);
        if (result.status === "completed") return result;
        if (result.status === "failed") {
            throw new Error(`Task failed: ${JSON.stringify(result.error)}`);
        }
        await new Promise((r) => setTimeout(r, interval));
        interval = Math.min(interval * 1.5, capMs);
    }
    throw new Error(`Task ${taskId} timed out after ${timeoutMs}ms`);
}
```

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

# 2. Poll
interval=2
for i in {1..30}; do
    result=$(curl -sS "$BASE/v1/images/tasks/$task_id" \
        -H "Authorization: Bearer $IMINI_API_KEY")
    status=$(echo "$result" | python3 -c 'import sys,json; print(json.load(sys.stdin).get("status",""))')
    echo "Poll $i: status=$status"
    case "$status" in
        completed) echo "$result"; exit 0 ;;
        failed) echo "$result" >&2; exit 1 ;;
    esac
    sleep $interval
    interval=$((interval * 3 / 2))
    [ $interval -gt 30 ] && interval=30
done

echo "Timed out" >&2
exit 2
```

---

## Notes for code generation

- Always read the API key from `process.env.IMINI_API_KEY` / `os.environ["IMINI_API_KEY"]`
- Keep the submit function and the polling loop as **separate functions** so callers can schedule them independently (e.g. submit many tasks, poll with a worker pool)
- When generating for a specific model, populate `model:` from the chosen model id and map body fields from the OpenAPI YAML's `properties:` list
- Include inline comments only where the YAML description adds non-obvious constraints (e.g. `prompt up to 6000 chars`)
- For video models with per-second pricing, add a cost estimate log line after successful completion
