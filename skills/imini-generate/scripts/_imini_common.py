#!/usr/bin/env python3
"""Shared helpers for the bundled imini scripts.

Python 3.8+ stdlib only. No third-party dependencies.

Functions used by generate_image.py / generate_video.py / poll_image_task.py /
poll_video_task.py. Centralizes submit / poll / upload / download / error
handling so per-script CLIs stay thin and protocol changes only need to be
made in one place.

This module does NOT hardcode any model IDs or per-model field names. Callers
build whatever JSON payload they want; the OpenAPI specs at
https://docs.imini.ai/en/openapi/ are the authority on field names per model.
"""
from __future__ import annotations

import base64
import json
import mimetypes
import os
import random
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

# ───────────────────────── constants ─────────────────────────

BASE_URL = "https://openapi.imini.ai/imini/router"
LLMS_URL = "https://docs.imini.ai/llms.txt"
USER_AGENT = "imini-skill-bundled/0.4.0"

# Submit endpoints
IMAGE_SUBMIT = "/v1/images/generate"
VIDEO_SUBMIT = "/v1/videos/generate"

# Query endpoint templates ({} = task_id)
IMAGE_QUERY = "/v1/images/tasks/{}"
VIDEO_QUERY = "/v1/videos/tasks/{}"

# Default hard timeouts — flat across all models, resolutions, durations.
IMAGE_TIMEOUT_DEFAULT = 600   # 10 min
VIDEO_TIMEOUT_DEFAULT = 1800  # 30 min

CACHE_TTL_SECONDS = 24 * 60 * 60  # 24 h


# ───────────────────────── exceptions ─────────────────────────

class IminiError(RuntimeError):
    """Any error originating from imini operations."""


class IminiHTTPError(IminiError):
    """Non-2xx HTTP response from the imini API."""

    def __init__(self, status: int, body: str, request_id: Optional[str] = None):
        self.status = status
        self.body = body
        self.request_id = request_id
        super().__init__(f"HTTP {status}: {body[:500]}")


# ───────────────────────── logging ─────────────────────────

class Logger:
    """Minimal stderr logger with quiet/verbose modes."""

    def __init__(self, quiet: bool = False, verbose: bool = False):
        self.quiet = quiet
        self.verbose = verbose

    def info(self, msg: str) -> None:
        if not self.quiet:
            print(msg, file=sys.stderr)

    def debug(self, msg: str) -> None:
        if self.verbose:
            print(f"  [debug] {msg}", file=sys.stderr)

    def warn(self, msg: str) -> None:
        print(f"⚠ {msg}", file=sys.stderr)

    def error(self, msg: str) -> None:
        print(f"✗ {msg}", file=sys.stderr)


# ───────────────────────── HTTP core ─────────────────────────

def _http_call(
    url: str,
    *,
    method: str = "GET",
    body: Optional[dict] = None,
    api_key: Optional[str] = None,
    timeout: int = 60,
) -> dict:
    headers = {"User-Agent": USER_AGENT}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    data: Optional[bytes] = None
    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")

    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
            if not raw:
                return {}
            return json.loads(raw)
    except urllib.error.HTTPError as e:
        body_text = e.read().decode("utf-8", errors="replace")
        request_id: Optional[str] = None
        try:
            err_obj = json.loads(body_text).get("error", {}) or {}
            request_id = err_obj.get("request_id")
        except Exception:
            pass
        raise IminiHTTPError(e.code, body_text, request_id) from e
    except urllib.error.URLError as e:
        raise IminiError(f"Network error: {e}") from e


def _jittered(interval: float) -> float:
    return interval * (0.8 + 0.4 * random.random())


# ───────────────────────── submit ─────────────────────────

def submit(
    endpoint: str,
    payload: dict,
    api_key: str,
    *,
    logger: Logger,
    max_retries: int = 3,
) -> dict:
    """POST a generation task.

    Retries on 429 and 5xx (up to max_retries). Surfaces 4xx (other than 429)
    immediately as IminiHTTPError so callers see structured imini errors.

    Returns the submit response envelope (must include `task_id`).
    """
    attempt = 0
    interval = 2.0
    while True:
        try:
            return _http_call(
                BASE_URL + endpoint,
                method="POST",
                body=payload,
                api_key=api_key,
                timeout=60,
            )
        except IminiHTTPError as e:
            transient = e.status == 429 or e.status >= 500
            if not transient or attempt >= max_retries:
                raise
            attempt += 1
            wait = max(_jittered(interval), 5.0 if e.status == 429 else interval)
            logger.warn(
                f"Submit got HTTP {e.status} (attempt {attempt}/{max_retries}), "
                f"retrying in {wait:.1f}s..."
            )
            time.sleep(wait)
            interval = min(interval * 1.5, 30.0)


# ───────────────────────── poll ─────────────────────────

def poll(
    query_template: str,
    task_id: str,
    api_key: str,
    *,
    start_interval: float = 2.0,
    cap_interval: float = 30.0,
    timeout: float = IMAGE_TIMEOUT_DEFAULT,
    logger: Logger,
) -> dict:
    """Poll a task until succeeded / failed / timeout.

    Returns the final task object on `succeeded`. Raises IminiError on
    `failed` (with full structured error info) or on timeout.

    Backoff: exponential ×1.5 capped at 30s, plus ±20% jitter. HTTP 429 bumps
    the floor to 5s. Transient 5xx responses are logged and retried.
    """
    deadline = time.monotonic() + timeout
    interval = start_interval
    last_status: Optional[str] = None

    while time.monotonic() < deadline:
        try:
            result = _http_call(
                BASE_URL + query_template.format(task_id),
                api_key=api_key,
                timeout=60,
            )
        except IminiHTTPError as e:
            if e.status == 429:
                logger.warn("Poll got HTTP 429, backing off ≥5s")
                interval = max(interval, 5.0)
            elif e.status >= 500:
                logger.warn(f"Poll got HTTP {e.status} (transient), continuing")
            else:
                raise
        else:
            status = result.get("status")
            if status != last_status:
                logger.info(f"  status: {status}")
                last_status = status

            if status == "succeeded":
                return result
            if status == "failed":
                err = result.get("error", {}) or {}
                raise IminiError(
                    f"Task {task_id} failed: "
                    f"{err.get('code', '?')} — {err.get('message', 'unknown')} "
                    f"[request_id={err.get('request_id', '?')}]"
                )
            # `queued` or `processing` — keep polling

        time.sleep(_jittered(interval))
        interval = min(interval * 1.5, cap_interval)

    raise IminiError(
        f"Task {task_id} did not complete within {timeout}s. "
        f"Last seen status: {last_status}. "
        f"Resume with poll_image_task.py / poll_video_task.py --task-id {task_id}."
    )


# ───────────────────────── file → data URL ─────────────────────────

_EXT_TO_MIME = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".gif": "image/gif",
    ".mp4": "video/mp4",
    ".webm": "video/webm",
    ".mov": "video/quicktime",
    ".mp3": "audio/mpeg",
    ".wav": "audio/wav",
    ".m4a": "audio/mp4",
    ".ogg": "audio/ogg",
}


def as_url(path_or_url: str) -> str:
    """Return a URL-shaped string suitable for imini's `url` reference field.

    - `http://...` / `https://...` → passed through unchanged.
    - `data:...` → passed through unchanged.
    - Anything else → treated as a local filesystem path, base64-encoded into
      a `data:<mime>;base64,...` URI. MIME is inferred from extension.

    Raises IminiError if the local path doesn't exist.
    """
    if path_or_url.startswith(("http://", "https://", "data:")):
        return path_or_url

    p = Path(path_or_url).expanduser().resolve()
    if not p.is_file():
        raise IminiError(f"Reference file not found: {path_or_url}")

    mime, _ = mimetypes.guess_type(str(p))
    if mime is None:
        mime = _EXT_TO_MIME.get(p.suffix.lower(), "application/octet-stream")

    payload = p.read_bytes()
    b64 = base64.b64encode(payload).decode("ascii")
    return f"data:{mime};base64,{b64}"


# ───────────────────────── download ─────────────────────────

def download(url: str, output_path: Path, *, logger: Logger) -> int:
    """Download `url` to `output_path`. Creates parent dirs. Returns bytes written."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = resp.read()
    output_path.write_bytes(data)
    logger.debug(f"wrote {len(data)} bytes → {output_path}")
    return len(data)


# ───────────────────────── API key ─────────────────────────

def resolve_api_key(cli_value: Optional[str], *, logger: Logger) -> str:
    """Resolve the imini API key from --api-key flag, then $IMINI_API_KEY.

    Raises IminiError with a clear message if neither is set. Warns when
    --api-key is used since it may be captured by shell history.
    """
    if cli_value:
        logger.warn(
            "--api-key on the command line is captured by your shell history. "
            "Prefer `export IMINI_API_KEY=...` and unset --api-key."
        )
        return cli_value
    key = os.environ.get("IMINI_API_KEY")
    if not key:
        raise IminiError(
            "IMINI_API_KEY environment variable not set.\n"
            "  Fix: export IMINI_API_KEY='sk-...' in your shell, then rerun.\n"
            "  Do NOT paste the key into chat — it will be logged in the conversation transcript.\n"
            "  Manage keys at https://imini.ai/api-keys."
        )
    return key


# ───────────────────────── catalog (cache + live) ─────────────────────────

def _cache_dir() -> Path:
    xdg = os.environ.get("XDG_CACHE_HOME")
    base = Path(xdg) if xdg else Path.home() / ".cache"
    d = base / "imini-generate"
    d.mkdir(parents=True, exist_ok=True)
    return d


def fetch_catalog(*, refresh: bool = False, logger: Logger, ttl: int = CACHE_TTL_SECONDS) -> str:
    """Return the contents of llms.txt.

    Strategy:
    - If cache exists and is younger than `ttl` seconds (and refresh=False),
      return cached content directly. Fast and offline-friendly.
    - Otherwise try to fetch live from `LLMS_URL`. On success, update cache.
    - On live fetch failure, fall back to whatever is in cache (any age),
      warning the user. If there's no cache either, raise.
    """
    cache_file = _cache_dir() / "llms.txt"
    cache_age = float("inf")
    if cache_file.is_file():
        cache_age = time.time() - cache_file.stat().st_mtime

    if not refresh and cache_age < ttl:
        logger.debug(f"using cached catalog (age: {int(cache_age)}s)")
        return cache_file.read_text("utf-8")

    try:
        logger.debug(f"fetching live catalog from {LLMS_URL}")
        req = urllib.request.Request(LLMS_URL, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=10) as resp:
            content = resp.read().decode("utf-8")
        cache_file.write_text(content, "utf-8")
        return content
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError) as e:
        if cache_file.is_file():
            logger.warn(
                f"Live catalog fetch failed ({e}); using cached copy "
                f"(age: {int(cache_age / 60)}min)."
            )
            return cache_file.read_text("utf-8")
        raise IminiError(f"Could not fetch catalog and no cache available: {e}")


# Catalog parsing — mirrors fetch_imini_catalog.py so we don't double-import
_LINE_RE = re.compile(
    r"^-\s+(?P<category>.+?)\s+"
    r"\[(?P<name>.+?)\]\((?P<doc_url>[^)]+)\):\s*"
    r"(?P<description>.*?)"
    r"(?:\s+Pricing[^:]*?:\s+(?P<pricing>.+?))?"
    r"(?:\s+Spec:\s+(?P<spec_url>\S+))?$"
)
_MODEL_ID_RE = re.compile(r"[a-z][a-z0-9_-]*/[a-z0-9.\-]+")
_TYPE_SECTIONS = {
    "Image Models (POST /v1/images/generate)": "image",
    "Video Models (POST /v1/videos/generate)": "video",
}


def parse_models(content: str, *, type_filter: Optional[str] = None) -> List[Dict[str, Any]]:
    """Parse llms.txt into a list of {model_id, name, type, pricing, spec_url, …}."""
    models: List[Dict[str, Any]] = []
    section_type: Optional[str] = None
    for raw_line in content.splitlines():
        s = raw_line.strip()
        if s.startswith("## "):
            section_type = _TYPE_SECTIONS.get(s[3:].strip())
            continue
        if not s.startswith("- ") or section_type is None:
            continue
        m = _LINE_RE.match(s)
        if not m:
            continue
        d = m.groupdict()
        mid = _MODEL_ID_RE.search(d.get("category") or "")
        if not mid:
            continue
        d["model_id"] = mid.group(0)
        d["type"] = section_type
        if type_filter and section_type != type_filter:
            continue
        models.append(d)
    return models


def format_model_list(models: List[Dict[str, Any]]) -> str:
    """Render parsed models for --list-models output."""
    lines: List[str] = []
    for m in models:
        lines.append(f"  {m['model_id']:40}  {m['name']}")
        desc = (m.get("description") or "").strip()
        if desc:
            if len(desc) > 140:
                desc = desc[:137] + "..."
            lines.append(f"    {desc}")
        if m.get("pricing"):
            lines.append(f"    pricing: {m['pricing']}")
        if m.get("spec_url"):
            lines.append(f"    spec:    {m['spec_url']}")
        lines.append("")
    return "\n".join(lines)


# ───────────────────────── output path resolution ─────────────────────────

def resolve_output_paths(
    output: Optional[Path],
    task_id: str,
    count: int,
    default_suffix: str,
) -> List[Path]:
    """Compute output file paths given user --output and how many results came back.

    - If `output` is None → use `<cwd>/<task_id>.<suffix>` (or numbered if multiple).
    - If `output` is a directory → save into it as `<task_id>-N.<suffix>`.
    - If `output` is a file path and count == 1 → use it as-is.
    - If `output` is a file path and count > 1 → insert `-N` before the suffix.
    """
    if output is None:
        if count == 1:
            return [Path(f"{task_id}{default_suffix}")]
        return [Path(f"{task_id}-{i}{default_suffix}") for i in range(count)]

    if output.is_dir() or str(output).endswith(os.sep):
        return [output / f"{task_id}-{i}{default_suffix}" for i in range(count)]

    if count == 1:
        return [output]

    stem = output.with_suffix("").name
    suffix = output.suffix or default_suffix
    parent = output.parent
    return [parent / f"{stem}-{i}{suffix}" for i in range(count)]


# ───────────────────────── extra JSON parsing ─────────────────────────

def parse_json_arg(value: Optional[str], *, flag_name: str) -> Dict[str, Any]:
    """Parse a JSON string from a CLI flag, returning {} for None.

    Raises IminiError with a friendly message on parse failure.
    """
    if not value:
        return {}
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as e:
        raise IminiError(f"{flag_name}: not valid JSON ({e}). Value was: {value!r}")
    if not isinstance(parsed, dict):
        raise IminiError(f"{flag_name}: expected a JSON object, got {type(parsed).__name__}")
    return parsed


# ───────────────────────── pretty payload preview ─────────────────────────

def preview_payload(payload: dict) -> str:
    """Dump payload as pretty JSON, redacting long data URIs for readability."""
    def redact(obj: Any) -> Any:
        if isinstance(obj, str) and obj.startswith("data:"):
            # Keep just the prefix so users can see something was attached.
            if len(obj) <= 64:
                return obj
            return f"{obj[:64]}...[truncated {len(obj) - 64} chars]"
        if isinstance(obj, dict):
            return {k: redact(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [redact(v) for v in obj]
        return obj

    return json.dumps(redact(payload), indent=2, ensure_ascii=False)
