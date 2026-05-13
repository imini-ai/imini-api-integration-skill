# Async task workflow

Every imini generation call follows the same pattern: submit a task, receive a `task_id`, then poll the task-query endpoint until the task is `succeeded` or `failed`. There is no synchronous generation endpoint.

## State machine

```
 [submit]  →  task_id + status=queued
                  │
                  ▼
         ┌────────────────────┐
         │  poll (GET /tasks) │
         └────────────────────┘
                  │
       ┌──────────┼──────────┐
       ▼          ▼          ▼
     queued   processing  succeeded / failed
       │          │
       └────┬─────┘
            ▼
       (re-poll after backoff)
```

Statuses returned by the task-query endpoint (exactly these four values):

- `queued` — submitted, waiting in queue
- `processing` — generating
- `succeeded` — result is ready; the payload contains output URL(s)
- `failed` — task failed; an `error` payload is included

> Terminal states are **`succeeded`** and **`failed`**. Do not check for `pending` / `completed` / `running` — those values are never returned.

## Endpoints

| Submit | Query |
|---|---|
| `POST /v1/images/generate` | `GET /v1/images/tasks/{task_id}` |
| `POST /v1/videos/generate` | `GET /v1/videos/tasks/{task_id}` |

Base URL for all endpoints: `https://openapi.imini.ai/imini/router`

## Authentication

Every request includes:

```
Authorization: Bearer <IMINI_API_KEY>
```

A single key works for every model. Get keys at https://imini.ai/api-keys.

## Recommended polling strategy

- **Start interval** — images: 2s; videos: 5s
- **Backoff** — exponential, multiplier 1.5, cap at 30s
- **Hard timeout** — images 10 min (600s), videos 30 min (1800s). Flat defaults across all models / resolutions / durations; see `errors.md` for the authoritative numbers
- **Jitter** — add ±20% jitter to the interval to avoid synchronized retries when many tasks are in flight
- **HTTP 429** — bump the next-interval floor to ≥5s before applying jitter

## Timeouts and retries

Classify failures:

- **Network error / connection reset** — retry with backoff (up to 3 attempts)
- **HTTP 429** — rate limit, back off longer (at least 5s)
- **HTTP 5xx** — transient server error, retry with backoff
- **HTTP 4xx (except 429)** — client error in payload; surface the full `error` object, do not retry

Do **not** retry `failed` tasks by re-polling — once a task is `failed`, submit a new task if needed.

## Concurrency

For batch workloads:

- Use a semaphore / worker pool to cap concurrent tasks
- Never spawn one thread per polling loop — use async or a shared poll worker
- Log `task_id` + `request_id` for traceability across retries
