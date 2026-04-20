# Model selection decision tree

Use this tree to pick the right imini model from the user's stated needs. Always confirm the choice with the user before generating code.

## Step 1 — image or video?

- Image → Section A
- Video → Section B

## A. Image models

### A.1 Pure text-to-image, want cheapest option, 1K is enough

→ **`google/nano-banana`**
- 1K only
- Up to 3 reference images (if needed)
- 50 credits / image (text-to-image), 100 credits / image (edit)

### A.2 Need 4K output, or need style reference (not just content reference)

→ **`google/nano-banana-pro`**
- 1K / 2K / 4K
- Up to 14 reference images
- Supports `reference_type: asset` (content) or `style`
- 120 / 120 / 200 credits per image (1K / 2K / 4K)

### A.3 Need flexible resolution tiers (including 512), want cost control

→ **`google/nano-banana-2`**
- 512 / 1K / 2K / 4K
- Up to 14 reference images
- 50 / 75 / 100 / 150 credits per image by tier
- Good default if unsure — most feature-complete Flash-series model

### Image quick picks

| User need | Recommended |
|---|---|
| Cheapest, 1K | `google/nano-banana` |
| 4K + style reference | `google/nano-banana-pro` |
| 512 thumbnail | `google/nano-banana-2` |
| Best all-around | `google/nano-banana-2` |

## B. Video models

### B.1 Reference video input required (video-guided generation)

→ **`kling/kling-v3-omni`** or **`doubao/seedance-2.0`** / **`doubao/seedance-2.0-fast`**
- `kling-v3-omni`: 720P / 1080P, optional audio, 120–220 credits/sec
- `seedance-2.0`: 480P / 720P, multimodal reference (image + video + audio); pricing scales with reference length
- `seedance-2.0-fast`: same capabilities as `seedance-2.0`, ~20% cheaper

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
- 120–220 credits / sec

### B.5 Cheapest video generation, 480P/720P acceptable

→ **`doubao/seedance-2.0-fast`**
- 80 credits/sec (480P), 160 credits/sec (720P) without reference video

### Video quick picks

| User need | Recommended |
|---|---|
| 1080P + reference video | `kling/kling-v3-omni` |
| 1080P + first/last frame | `kling/kling-v3` |
| Multimodal reference (img+video+audio) | `doubao/seedance-2.0` |
| Cheapest | `doubao/seedance-2.0-fast` |

## Cost estimation helpers

### Image: credits per image (by resolution)

| Model | 512 | 1K | 2K | 4K | Edit (non-T2I) |
|---|---|---|---|---|---|
| `google/nano-banana` | — | 50 | — | — | 100 |
| `google/nano-banana-pro` | — | 120 | 120 | 200 | same as T2I |
| `google/nano-banana-2` | 50 | 75 | 100 | 150 | same as T2I |

### Video: credits per output second (no reference video)

| Model | 480P | 720P no audio | 720P with audio | 1080P no audio | 1080P with audio |
|---|---|---|---|---|---|
| `kling/kling-v3` | — | 120 | 170 | 160 | 220 |
| `kling/kling-v3-omni` (no ref video) | — | 120 | 160 | 160 | 200 |
| `kling/kling-v3-omni` (with ref video) | — | 170 | — | 220 | — |
| `doubao/seedance-2.0` (no ref video) | 100 | 200 | — | — | — |
| `doubao/seedance-2.0-fast` (no ref video) | 80 | 160 | — | — | — |

For Seedance with a reference video, pricing scales with total reference length + output duration — point the user to https://docs.imini.ai/en/guide/pricing for exact numbers.

### Typical totals

- Single 1K image: 50–120 credits
- 5-second 1080P Kling video (no audio): ~800 credits
- 10-second 720P Seedance Fast video: ~1,600 credits
