---
name: imini-api-integration
description: Use this skill whenever the user needs to integrate AIGC image or video generation into code — text-to-image, image editing with references, text-to-video, image-to-video, first/last frame, reference video, or multimodal (image + video + audio) generation. Auto-selects the right imini model, estimates credit cost, and generates production-ready asynchronous task code (submit + poll). Triggers on mentions of imini, openapi.imini.ai, or any imini model id (nano-banana, nano-banana-pro, nano-banana-2, kling-v3, kling-v3-omni, seedance-2.0, seedance-2.0-fast).
---

# imini Open Platform API Integration

Integrate imini's AIGC image and video generation APIs into any project. Pick the right model, estimate cost, and generate complete asynchronous task code.

## About imini

imini offers AIGC image and video generation APIs under:

- **Unified endpoint**: `https://openapi.imini.ai/imini/router`
- **Unified auth**: one Bearer API key works for every model
- **Unified async pattern**: every generation call returns a `task_id`; poll the task-query endpoint until `status` is `succeeded` or `failed`. The four possible values are `queued` / `processing` / `succeeded` / `failed` — do NOT check for `pending` / `completed` / `running`, those strings are never returned.
- **Unified error shape**: `{ error: { code, message, status, request_id } }`

## When to use this skill

Use **proactively** whenever the user:

- Wants to generate or edit an image (text-to-image, asset/style reference)
- Wants to generate a video from text, image(s), first/last frames, a reference video, or a multimodal bundle (image + video + audio)
- Mentions `imini`, `openapi.imini.ai`, or any imini model id
- Asks about async generation / polling patterns for AI media
- Asks to estimate credit cost for generation workloads

## Workflow

### Step 1. Get the user's imini API key

Ask the user for their imini API key. Mention that all imini models share a single key:

- English: https://imini.ai/api-keys
- 中文: https://imini.ai/zh/api-keys

**Never hard-code the key into generated code.** Always use an environment variable (default: `IMINI_API_KEY`).

### Step 2. Clarify intent

Ask only what's needed to pick a model:

1. **Image or video?**
2. **Input modalities**: text only / reference images / first-and-last frame / reference video / multimodal (image + video + audio)?
3. **Quality tier**: for images — 1K / 2K / 4K (or 512 for nano-banana-2); for videos — 480P / 720P / 1080P
4. **Duration** (video only)
5. **Programming language** the user is integrating into

Skip any question the user has already answered.

### Step 3. Load the latest catalog

**Always use the script — do NOT WebFetch `llms.txt` directly.** The script parses the catalog into structured records and keeps context compact:

```bash
# List every model with capability and pricing hints
python3 scripts/fetch_imini_catalog.py

# Filter by type
python3 scripts/fetch_imini_catalog.py --type image
python3 scripts/fetch_imini_catalog.py --type video

# Look up one model
python3 scripts/fetch_imini_catalog.py --model google/nano-banana-pro

# JSON for programmatic use
python3 scripts/fetch_imini_catalog.py --json
```

The script fetches `https://docs.imini.ai/llms.txt` live, so users always see the latest supported models without reinstalling the skill.

### Step 4. Recommend model(s) and estimate cost

Use `references/model_selection.md` as the decision tree. Present 1–2 candidates with:

- Model ID
- Why it fits (capability alignment)
- Approximate credit cost for the user's scenario
- For Seedance with reference video: pricing scales with reference length — link to https://docs.imini.ai/en/guide/pricing for the detailed table

Get explicit confirmation before generating code.

### Step 5. Fetch the full OpenAPI spec

Once the model is confirmed, WebFetch the `Spec:` URL from the catalog record, which points to the YAML endpoint — e.g.:

```
https://docs.imini.ai/en/openapi/images/nano-banana-pro.yaml
```

Use the YAML endpoint (not the `.md` endpoint) — it's clean OpenAPI 3.1.0 and parses deterministically.

### Step 6. Generate the integration code

Use the templates in `references/integration_examples.md`. Every generated code bundle MUST include:

1. **Submit function** — POST to the generation endpoint, return `task_id`
2. **Polling loop** — GET the task-query endpoint with exponential backoff until `status === "succeeded"` or `status === "failed"`, with a hard timeout. Never branch on `completed` / `running` — those values do not exist in this API.
3. **Result extraction** — image tasks return `images[].url`; video tasks return `videos[].url` (plus `width`, `height`, and for videos `duration`). Always read the array even if it has a single element.
4. **Error handling** — see `references/errors.md`

Supported output languages (initial):

- Python (sync and async)
- Node.js
- TypeScript
- cURL (two-step: submit + poll)

### Step 7. Explain and give production tips

- Wire the key via environment variable, never hard-code
- Polling start interval: images ~2s, videos ~5s; exponential backoff to a cap
- Timeout defaults: images ~60s, videos up to ~600s depending on duration
- Concurrency: use a semaphore or worker pool — don't block on sync polling loops in parallel
- Cost control: log `task_id` + estimated credit cost per submission; set per-user quotas upstream

## Reference files

- `references/workflow.md` — async task state machine and polling details
- `references/model_selection.md` — decision tree from user needs to model
- `references/integration_examples.md` — code templates per language
- `references/errors.md` — error codes and retry strategy
- `scripts/fetch_imini_catalog.py` — catalog fetcher/parser

## External resources

- Platform: https://imini.ai
- Docs: https://docs.imini.ai
- Pricing: https://docs.imini.ai/en/guide/pricing
- Changelog: https://docs.imini.ai/en/changelog
- Support: support@imini.com
