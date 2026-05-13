# Error handling

imini returns a uniform error envelope for every failure:

```json
{
  "error": {
    "code": "INVALID_PROMPT",
    "message": "Prompt contains disallowed content",
    "status": 400,
    "request_id": "req_abc123"
  }
}
```

Always log `request_id` — imini support will ask for it.

## HTTP status reference

| Status | Meaning | Retry? |
|---|---|---|
| 200 | Success | — |
| 400 | Validation error (bad params, disallowed content) | **No** — surface to user |
| 401 | Invalid / missing API key | **No** — ask user to check key |
| 403 | Forbidden (insufficient permission / quota exhausted) | **No** — surface |
| 404 | Task not found (task-query only) | **No** — likely invalid `task_id` |
| 429 | Rate limit exceeded | **Yes** — exponential backoff, longer initial delay |
| 5xx | Transient server error | **Yes** — exponential backoff |
| Network error | Connection reset / DNS / timeout | **Yes** — up to 3 attempts |

## Common error codes

| Code | When | What to do |
|---|---|---|
| `INVALID_PROMPT` | Prompt rejected by content policy | Ask user to adjust the prompt |
| `INVALID_PARAMETER` | A body field is out of range or missing | Check against the OpenAPI spec |
| `INSUFFICIENT_CREDITS` | Account balance too low | Top up at https://imini.ai |
| `RATE_LIMITED` | Too many requests in a short window | Back off, retry |
| `TASK_NOT_FOUND` | `task_id` invalid or expired | Re-submit the task |

Error codes may evolve — always fall back to displaying `error.code` + `error.message` verbatim if an unknown code appears.

## Retry policy

**Exponential backoff with jitter**:

```
delay = min(cap, base * 1.5^attempt) * (0.8 + 0.4 * random())
```

- `base` = 2s for images, 5s for videos, 5s for 429
- `cap` = 30s
- Max attempts: 3 for network / 5xx, unlimited for polling during task execution (guarded by task-level timeout instead)

**Never retry**:

- 4xx other than 429 — caller needs to fix the request
- A task whose status is already `failed` — re-submit instead

## Task-level timeout guidance

Keep one **hard timeout** per task, measured from submit to `succeeded`. Polling retries share the budget.

The bundled scripts use **flat defaults — no per-resolution / per-duration scaling**:

| Type | Default hard timeout |
|---|---|
| Image (any model, any resolution) | **600s (10 min)** |
| Video (any model, any duration, with or without reference video) | **1800s (30 min)** |

These are generous upper bounds — most calls complete in seconds for images and 30–120s for videos. The defaults exist to absorb queue depth and cold-start variance. Override with `--timeout SECONDS` per call if your environment is tighter (e.g. an interactive UI that wants to fail fast) or looser (e.g. long-duration video with a heavy reference video that genuinely needs more headroom).

These two numbers are the **authoritative defaults** — `SKILL.md` and `workflow.md` defer to them. They are also the values of `IMINI_IMAGE_TIMEOUT_DEFAULT` and `VIDEO_TIMEOUT_DEFAULT` in `scripts/_imini_common.py`; change those constants if you want a different default everywhere.

## Logging checklist

For every submit + poll round, log:

- `model` (e.g. `google/nano-banana-pro`)
- `task_id`
- `request_id` of every HTTP call
- Final `status` (`succeeded` / `failed` / timeout)
- Elapsed time from submit to completion
- Estimated credit cost (derived at submit time from the pricing tables)
