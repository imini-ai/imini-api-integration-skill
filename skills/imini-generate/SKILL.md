---
name: imini-generate
description: Use this skill whenever the user needs to generate, edit, or integrate AIGC images or videos with imini Open Platform — text-to-image, image editing with references, text-to-video, image-to-video, first/last frame, reference video, motion control, video editing, or multimodal generation. Two paths — (A) ad-hoc one-shot generation right now via bundled Python scripts (no codegen, no token burn for re-deriving submit/poll logic); (B) writing async integration code into the user's own project. Triggers on mentions of imini, openapi.imini.ai, or any imini model id (nano-banana, nano-banana-pro, nano-banana-2, gpt-image-2, kling-v3, kling-v3-omni, kling-v3-motion-control, seedance-2.0, seedance-2.0-fast, happyhorse-1.0).
---

# imini Open Platform API Integration

Generate images / videos with imini, OR write integration code for the user's project. Pick the right model, estimate cost, handle async tasks.

## About imini

- **Unified endpoint**: `https://openapi.imini.ai/imini/router`
- **Unified auth**: one Bearer API key works for every model — `Authorization: Bearer $IMINI_API_KEY`
- **Unified async pattern**: every generation call returns a `task_id`; poll the task-query endpoint until `status` is `succeeded` or `failed`. **The four possible values are `queued` / `processing` / `succeeded` / `failed`** — never check for `pending` / `completed` / `running`.
- **Unified error shape**: `{ error: { code, message, status, request_id } }`
- **Catalog**: https://docs.imini.ai/llms.txt — always up-to-date model list with pricing and per-model OpenAPI spec URLs

## Step 0 — Route to the right path

Two paths. Pick before doing anything else.

| User says... | Path | What you do |
|---|---|---|
| "Generate / make / draw / create [image \| video] of …" | **A** | Run a bundled script — no codegen |
| "Try imini with this prompt" / "show me what … looks like" | **A** | Same |
| "Add imini to my project / app / backend" | **B** | Generate code templates in user's language |
| "Write a Python/Node/TS function that calls imini" | **B** | Same |
| "Test if imini can do X" | **A** then ask whether they also need code | |
| User is unclear | Ask: "One-off generation now, or integration code for your project?" | |

The two paths share knowledge about models (`references/model_selection.md`) but **only Path B needs to read `references/integration_examples.md`**. Skipping that file in Path A is the main token-efficiency win.

---

## Path A — One-shot generation (bundled scripts)

The skill ships executable Python scripts that handle submit + poll + 429/5xx retry + jitter + structured error preservation + result download. You call them; you do not rewrite this logic in throwaway Python every session.

### A1 — Preflight

Before running any script:

1. **Check Python**: `python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3,8) else 1)'` — must succeed. If it fails, tell the user to install Python 3.8+ (macOS: built-in; Ubuntu: `sudo apt install python3`; Windows: `winget install Python.Python.3`).
2. **Check API key**: `[ -n "$IMINI_API_KEY" ] && echo OK || echo MISSING`. If missing, instruct the user to **set it in their shell** (`export IMINI_API_KEY='sk-...'`) — **do not** ask them to paste the key into the conversation, it would end up in the agent's transcript. Keys are managed at https://imini.ai/api-keys.

### A2 — Pick a model (live-fetched, never hardcoded)

If the user has not named a model, run:

```bash
python3 ${SKILL_DIR}/scripts/generate_image.py --list-models    # for images
python3 ${SKILL_DIR}/scripts/generate_video.py --list-models    # for videos
```

This pulls the catalog from `https://docs.imini.ai/llms.txt` (with a 24h offline cache) and prints model IDs, capability summaries, pricing, and OpenAPI spec URLs. **Do not maintain a hardcoded model list anywhere** — new models become available as soon as imini publishes them.

For deciding which model fits a stated need, consult `references/model_selection.md`. For exact pricing of complex scenarios (Seedance with reference video etc.), point to https://docs.imini.ai/en/guide/pricing.

### A3 — Run the script

Image (one image, 1080p-ish, 4K res):

```bash
python3 ${SKILL_DIR}/scripts/generate_image.py \
    --model google/nano-banana-pro \
    --prompt "a moody cinematic portrait at golden hour" \
    --resolution 4K --aspect-ratio 16:9 \
    --output ./out.png
```

Image with style + asset references:

```bash
python3 ${SKILL_DIR}/scripts/generate_image.py \
    --model google/nano-banana-pro \
    --prompt "place the product in this style" \
    --style-reference ./mood.jpg \
    --reference-image ./product.png \
    --resolution 2K --aspect-ratio 1:1 \
    --output ./out.png
```

Video (5-second 1080p with audio):

```bash
python3 ${SKILL_DIR}/scripts/generate_video.py \
    --model kling/kling-v3 \
    --prompt "drone shot over snowy mountains at sunrise" \
    --duration 5 --resolution 1080P --aspect-ratio 16:9 \
    --audio \
    --output ./drone.mp4
```

Video with first + last frame interpolation:

```bash
python3 ${SKILL_DIR}/scripts/generate_video.py \
    --model kling/kling-v3 \
    --prompt "smooth camera move from sunrise to sunset" \
    --start-image ./first.jpg --end-image ./last.jpg \
    --duration 10 --resolution 720P \
    --output ./interp.mp4
```

Long-running video — fire and walk away:

```bash
# Submit only, returns task_id immediately
TASK_ID=$(python3 ${SKILL_DIR}/scripts/generate_video.py \
    --model doubao/seedance-2.0 \
    --prompt "..." --duration 15 --resolution 720P \
    --reference-video ./ref.mp4 \
    --async)
echo "task_id: $TASK_ID"

# Later — resume polling and download
python3 ${SKILL_DIR}/scripts/poll_video_task.py --task-id "$TASK_ID" --output ./out.mp4
```

### A4 — Common CLI patterns

All four scripts share these flags:

- `--print-request` — print the JSON body that *would* be sent, then exit. No API key needed. Useful for sanity-checking before committing credits.
- `--no-download` — skip the file download, print result URLs to stdout instead.
- `--quiet` — only emit the final saved path.
- `--verbose` — show debug-level polling detail.
- `--api-key KEY` — override `$IMINI_API_KEY` (discouraged; captured by shell history).
- `--timeout SECONDS` — override the default hard timeout. Defaults are flat: 600s (10 min) for any image, 1800s (30 min) for any video. See `references/errors.md` for the authoritative numbers.
- `--list-models` — fetch and print current models from llms.txt (24h cache).
- `--refresh-cache` — force a live re-fetch of llms.txt.

For fields not surfaced as explicit flags, use the escape hatches:

- `--extra '<json>'` — merges into the request body at root level.
- `--extra-params '<json>'` (video only) — merges into `extra_params` (Kling multi-shot, camera_control, negative_prompt, etc.; happyhorse audio_setting).

### A5 — Report results to the user

After the script exits successfully it prints `saved → <path>  (<bytes>, <wxh>)`. Surface the saved path(s), the model used, the duration/resolution metadata, and the approximate credit cost (from the catalog) so the user knows what they spent.

For multi-image results (`--num-images > 1`), iterate the file paths the script saved — do not assume `[0]`.

---

## Path B — Integration code for the user's project

When the user wants imini *embedded in their own codebase*, not a one-off file in their cwd, generate code templates.

### B1 — Get the API key

Confirm the user has an imini API key. Direct them to https://imini.ai/api-keys . **Never hard-code the key into generated code.** All templates must read it from an environment variable (default name: `IMINI_API_KEY`).

### B2 — Clarify intent

Ask only the questions needed to pick a model:

1. Image or video?
2. Input modalities: text only / reference images / first-and-last frame / reference video / multimodal?
3. Quality tier (image: 1K / 2K / 4K / 512; video: 480P / 720P / 1080P)
4. Duration (video only)
5. Programming language they're integrating into (Python / Node / TypeScript / cURL)

### B3 — Pick a model

Use the live catalog the same way as Path A (`scripts/generate_image.py --list-models` or `scripts/fetch_imini_catalog.py`) plus `references/model_selection.md` as the capability decision tree. Present 1–2 candidates with model ID, capability fit, and credit cost. Get explicit confirmation before writing code.

### B4 — Fetch the OpenAPI spec

For the chosen model, fetch the YAML at its `Spec:` URL (e.g. `https://docs.imini.ai/en/openapi/images/nano-banana-pro.yaml`). Use whatever HTTP fetch tool your agent has, or fall back to `curl`. The YAML form is clean OpenAPI 3.1.0 and parses deterministically — prefer it over the `.md` form.

### B5 — Generate code

Use the templates in `references/integration_examples.md`. Every generated code bundle MUST include:

1. **Submit function** — POST to the generation endpoint, return `task_id`.
2. **Polling loop** — GET the task-query endpoint with exponential backoff, ±20% jitter, 429 floor of 5s, hard timeout. Branch on `succeeded` and `failed` only — never `completed` / `running`.
3. **Result extraction** — image tasks return `images[]`; video tasks return `videos[]`. Each element has `url` plus `width` / `height` (videos also `duration`). **Always iterate the array — never hardcode `[0]`.** Some models / parameters produce multiple outputs.
4. **Structured error preservation** — surface `error.code`, `error.message`, `error.request_id` on failures so the user can log `request_id` for imini support.

Supported template languages:

- Python (sync, stdlib only — `urllib`)
- Python (async, requires `aiohttp ≥ 3.9`)
- Node.js (requires **Node 18+** for native `fetch`)
- TypeScript (requires Node 18+)
- cURL (two-step: submit + poll, with `python3 -c` for JSON parsing)

### B6 — Production tips

- API key via environment variable, never hard-coded.
- Polling start interval: images ~2s, videos ~5s. Exponential backoff ×1.5 capped at 30s, plus ±20% jitter.
- On HTTP 429: bump backoff floor to ≥5s before the next attempt.
- Timeouts: see `references/errors.md` for the authoritative per-scenario table.
- Concurrency: use a semaphore or worker pool — don't block on synchronous polling in parallel.
- Cost control: log `task_id` + estimated credit cost per submission; set per-user quotas upstream.

---

## Reference files

- `references/workflow.md` — async task state machine and polling strategy details
- `references/model_selection.md` — capability decision tree (model picking)
- `references/integration_examples.md` — Path B code templates per language
- `references/errors.md` — authoritative timeout table + error codes + retry policy
- `scripts/_imini_common.py` — shared submit/poll/upload/download/error logic (used by all bundled scripts)
- `scripts/generate_image.py` — Path A: image generation CLI
- `scripts/generate_video.py` — Path A: video generation CLI
- `scripts/poll_image_task.py` — resume an image task_id
- `scripts/poll_video_task.py` — resume a video task_id
- `scripts/fetch_imini_catalog.py` — original catalog fetcher (`--list-models` in generate scripts wraps the same logic)

## External resources

- Platform: https://imini.ai
- Docs: https://docs.imini.ai
- Pricing: https://docs.imini.ai/en/guide/pricing
- Changelog: https://docs.imini.ai/en/changelog
- Support: support@imini.com
