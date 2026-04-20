# imini API Integration Skill

> The official Claude Code skill for imini open platform — AIGC image and video generation APIs.

Helps developers integrate imini's image and video generation APIs into any codebase. Automatically picks the right model, estimates credit cost, and generates production-ready **asynchronous task** code — the submit + polling flow, not just an HTTP snippet.

[中文版 README](./README_CN.md)

## Install

Share this repository URL with Claude Code:

```
https://github.com/imini-ai/imini-api-integration-skill
```

Claude Code installs it as a skill. Verify with:

```
What skills are available?
```

## What it does

- **Auto model selection** — describe what you want to generate; the skill picks the right imini model
- **Always up-to-date** — model list fetched live from `docs.imini.ai/llms.txt`; **no reinstall needed when imini ships new models**
- **Complete async flow** — submit function + polling loop + result extraction + timeout, not just a POST call
- **Multi-language output** — Python (sync + async), Node.js, TypeScript, cURL
- **Cost estimation** — credit estimate for the user's scenario before they run it
- **Built-in error handling** — retry on 429 / 5xx with exponential backoff, surface 4xx with full error shape

## Supported models

| Model ID | Type | Underlying | Strengths |
|---|---|---|---|
| `google/nano-banana` | image | Gemini 2.5 Flash Image | Fast, low-cost, 1K |
| `google/nano-banana-pro` | image | Gemini 3 Pro Image | Up to 4K, 14 reference images, asset/style refs |
| `google/nano-banana-2` | image | Gemini 3.1 Flash Image | 512 / 1K / 2K / 4K tiers, 14 ref images |
| `kling/kling-v3` | video | Kling 3.0 | Text/image to video, first-last-frame, multi ref images |
| `kling/kling-v3-omni` | video | Kling 3.0 Omni | Adds reference-video input on top of v3 |
| `doubao/seedance-2.0` | video | Seedance 2.0 | Multimodal reference (image + video + audio) |
| `doubao/seedance-2.0-fast` | video | Seedance 2.0 Fast | Same features as 2.0, lower cost |

Live catalog: https://docs.imini.ai/llms.txt

## Example prompts

### Text-to-image in Python

> "I want to generate a 4K cinematic image from a prompt using imini's best image model, in Python."

The skill picks `google/nano-banana-pro`, fetches the spec, and generates Python code with env-var auth, a submit function, a polling loop with exponential backoff, and result extraction.

### Image-to-video with a reference video in Node.js

> "Generate a 10-second 1080P video with a reference video driving the style, using imini in Node.js."

The skill picks `kling/kling-v3-omni` (or `doubao/seedance-2.0` / `seedance-2.0-fast` for a cheaper multimodal alternative), estimates the credit cost, and generates Node.js code.

### Batch generation with concurrency

> "Generate 100 images in parallel but cap concurrency at 10."

The skill generates async Python with `aiohttp` + a semaphore, polling, and rate-limit retry.

## API key

Get your imini API key (one key for every model) at:

- https://imini.ai/api-keys (English)
- https://imini.ai/zh/api-keys (中文)

**Security**: the generated code always reads the key from the `IMINI_API_KEY` environment variable — never hard-coded.

## Requirements

- Python 3.8+ (catalog script uses stdlib only — no `pip install` needed)
- Claude Code

## Links

- Platform: https://imini.ai
- API docs: https://docs.imini.ai
- Pricing: https://docs.imini.ai/en/guide/pricing
- Changelog: https://docs.imini.ai/en/changelog
- Support: support@imini.com

## License

MIT — see [LICENSE](./LICENSE).
