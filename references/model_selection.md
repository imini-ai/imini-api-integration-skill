# Model selection decision tree

Use this tree to pick the right imini model from the user's stated needs. Always confirm the choice with the user before generating code.

> **Capability vs. price**: this file is the **capability** map (which model can do what). For **live pricing**, run the catalog script — it parses `Pricing:` from `llms.txt` so the numbers stay fresh:
>
> ```bash
> python3 scripts/fetch_imini_catalog.py --type image
> python3 scripts/fetch_imini_catalog.py --type video
> python3 scripts/fetch_imini_catalog.py --model openai/gpt-image-2
> ```
>
> For totals across complex scenarios (Seedance with reference video, etc.), see https://docs.imini.ai/en/guide/pricing.

## Step 1 — image or video?

- Image → Section A
- Video → Section B

## A. Image models

### A.1 Pure text-to-image, want cheapest option, 1K is enough

→ **`google/nano-banana`**
- 1K only
- Up to 3 reference images (if needed)
- Cheapest Gemini Flash Image option

### A.2 Need 4K output, or need style reference (not just content reference)

→ **`google/nano-banana-pro`**
- 1K / 2K / 4K
- Up to 14 reference images
- Supports `reference_type: asset` (content) or `style`

### A.3 Need flexible resolution tiers (including 512), want cost control

→ **`google/nano-banana-2`**
- 512 / 1K / 2K / 4K
- Up to 14 reference images
- Good default if unsure — most feature-complete Flash-series model

### A.4 Need OpenAI's gpt-image-2 (independent quality knob)

→ **`openai/gpt-image-2`**
- 1K / 2K / 4K resolutions × `low` / `medium` / `high` quality (orthogonal — 9 combinations)
- Up to 3 reference images (asset references)
- Pick this when the user explicitly wants the OpenAI model, or needs a quality tier independent of resolution
- Pricing has the widest range of any image model — `4K + high` is the most expensive single image call across the catalog

### Image quick picks

| User need | Recommended |
|---|---|
| Cheapest, 1K | `google/nano-banana` |
| 4K + style reference | `google/nano-banana-pro` |
| 512 thumbnail | `google/nano-banana-2` |
| Quality tier independent of resolution | `openai/gpt-image-2` |
| Best all-around | `google/nano-banana-2` |

## B. Video models

### B.1 Reference video input required (video-guided generation)

→ **`kling/kling-v3-omni`** or **`doubao/seedance-2.0`** / **`doubao/seedance-2.0-fast`**
- `kling-v3-omni`: 720P / 1080P, optional audio
- `seedance-2.0`: 480P / 720P, multimodal reference (image + video + audio); pricing scales with reference length
- `seedance-2.0-fast`: same capabilities as `seedance-2.0`, lower cost

Pick `kling-v3-omni` for 1080P output; pick `seedance-2.0-fast` when 720P is enough and cost matters.

### B.2 First-and-last-frame control

→ **`kling/kling-v3`** (720P / 1080P) or **`doubao/seedance-2.0`** (480P / 720P)

Pick Kling when 1080P is required; pick Seedance for cheaper 480P.

### B.3 Multimodal reference (image + video + audio in one request)

→ **`doubao/seedance-2.0`** or **`doubao/seedance-2.0-fast`**
- Only the Seedance family supports audio reference input

### B.4 Basic text-to-video or image-to-video, 720P/1080P

→ **`kling/kling-v3`**
- Text-to-video, image-to-video, multi-reference-image
- 720P / 1080P, optional audio

### B.5 Cheapest video generation, 480P/720P acceptable

→ **`doubao/seedance-2.0-fast`** without reference video

### B.6 Motion control — replicate motion from a reference video onto a character

→ **`kling/kling-v3-motion-control`**
- Takes **1 reference image** (character) + **1 reference video** (motion source); replicates the motion onto the character
- 720P / 1080P
- Use when the user wants to drive a stylized character with motion captured from real footage; **not** for general text-to-video — for that use `kling/kling-v3`

### B.7 Single model covering text-to-video, image-to-video, reference-to-video, AND video editing

→ **`dashscope/happyhorse-1.0`**
- One model id covers: text-to-video, image-to-video (first frame), reference-to-video (1–9 asset images referenced via `character1` / `character2` … in the prompt), and video editing (1 reference video + 0–5 reference images)
- Audio handling via `extra_params.audio_setting`
- 720P / 1080P, duration 3–15s (video edit follows source video length, capped at 15s)
- Pick this when the user wants one model id for many scenarios, or when they need video **editing** (other models in the catalog don't do editing)

### Video quick picks

| User need | Recommended |
|---|---|
| 1080P + reference video | `kling/kling-v3-omni` |
| 1080P + first/last frame | `kling/kling-v3` |
| Multimodal reference (img+video+audio) | `doubao/seedance-2.0` |
| Cheapest | `doubao/seedance-2.0-fast` |
| Motion control (character + motion) | `kling/kling-v3-motion-control` |
| Video editing (modify existing footage) | `dashscope/happyhorse-1.0` |
| One model for many scenarios | `dashscope/happyhorse-1.0` |

## Cost estimation

Pricing is fetched live from `llms.txt`. For any model, run:

```bash
python3 scripts/fetch_imini_catalog.py --model <provider>/<model-id>
```

The script prints the `Pricing:` line straight from the catalog so it never falls out of sync with the platform. For Seedance with a reference video and other multi-factor scenarios, see https://docs.imini.ai/en/guide/pricing for the detailed tables.

### Typical orders of magnitude (rule-of-thumb only — verify with the script)

| Scenario | Order of magnitude |
|---|---|
| Single 1K image (Flash family) | ~50–120 credits |
| Single 4K image (Pro / high quality) | ~200–1000 credits |
| 5-second 1080P video (no audio, no reference) | ~600–1100 credits |
| 10-second 720P fast video | ~1,600 credits |
| Motion control 5s @ 1080P | ~1,100 credits |
| HappyHorse 5s @ 1080P | ~1,500 credits |

Use these to flag obviously-wrong cost estimates ("oh, 50 credits for a 10s 1080P video" → no, that's three orders of magnitude off). For exact totals, run the script.
