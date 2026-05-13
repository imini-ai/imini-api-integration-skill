#!/usr/bin/env python3
"""Submit and (by default) poll an imini video generation task.

Stdlib only (Python 3.8+). No model IDs or per-model field lists are
hardcoded — passing `--list-models` reads from llms.txt (live, with 24h
cache fallback). For any field this CLI doesn't surface explicitly, use
`--extra '<json>'` (root-level merge) or `--extra-params '<json>'`
(merge into `extra_params`, used by Kling for multi-shot / camera
controls etc.).

Example:
    export IMINI_API_KEY='sk-...'
    python3 generate_video.py \\
        --model kling/kling-v3 \\
        --prompt "drone shot over a snowy mountain range at sunrise" \\
        --duration 5 --resolution 1080P --aspect-ratio 16:9 \\
        --output ./drone.mp4
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

import _imini_common as imini


def build_payload(args: argparse.Namespace) -> Dict[str, Any]:
    """Translate CLI flags into the JSON body for POST /v1/videos/generate.

    Reference images use the `reference_images: [{url, reference_type}]` shape
    (per kling-v3 / seedance-2.0 specs). first/last frame are encoded as
    reference_type=first_frame / last_frame; other refs default to asset.

    motion-control models (e.g. kling/kling-v3-motion-control) take a
    character image plus a motion video — surfaced as --character-image /
    --motion-video. Field names may vary; use --extra to override.
    """
    payload: Dict[str, Any] = {"model": args.model}

    if args.prompt is not None:
        payload["prompt"] = args.prompt

    if args.resolution:
        payload["resolution"] = args.resolution
    if args.aspect_ratio:
        payload["aspect_ratio"] = args.aspect_ratio
    if args.duration is not None:
        payload["duration"] = args.duration
    if args.audio:
        payload["generate_audio"] = True

    # Build reference_images list from start/end/asset flags
    references: List[Dict[str, str]] = []
    if args.start_image:
        references.append({"url": imini.as_url(args.start_image), "reference_type": "first_frame"})
    if args.end_image:
        references.append({"url": imini.as_url(args.end_image), "reference_type": "last_frame"})
    for path in (args.reference_image or []):
        references.append({"url": imini.as_url(path), "reference_type": "asset"})
    if references:
        payload["reference_images"] = references

    if args.reference_video:
        payload["reference_video"] = imini.as_url(args.reference_video)

    # Motion control (kling-v3-motion-control)
    if args.character_image:
        payload["character_image"] = imini.as_url(args.character_image)
    if args.motion_video:
        payload["motion_video"] = imini.as_url(args.motion_video)

    # extra_params (Kling multi-shot, camera_control, etc.; happyhorse audio_setting)
    extra_params = imini.parse_json_arg(args.extra_params, flag_name="--extra-params")
    if args.audio_setting:
        extra_params.setdefault("audio_setting", json.loads(args.audio_setting)
                                if args.audio_setting.strip().startswith("{")
                                else args.audio_setting)
    if extra_params:
        payload["extra_params"] = extra_params

    # Root-level escape hatch
    payload.update(imini.parse_json_arg(args.extra, flag_name="--extra"))

    return payload


def cmd_list_models(args: argparse.Namespace) -> int:
    logger = imini.Logger(quiet=args.quiet, verbose=args.verbose)
    content = imini.fetch_catalog(refresh=args.refresh_cache, logger=logger)
    models = imini.parse_models(content, type_filter="video")
    if not models:
        logger.error("No video models found in catalog.")
        return 2
    print(f"Video models available on imini (catalog from {imini.LLMS_URL}):\n")
    print(imini.format_model_list(models))
    return 0


def cmd_generate(args: argparse.Namespace) -> int:
    logger = imini.Logger(quiet=args.quiet, verbose=args.verbose)

    payload = build_payload(args)

    if args.print_request:
        print(imini.preview_payload(payload))
        return 0

    api_key = imini.resolve_api_key(args.api_key, logger=logger)

    logger.info(f"→ Submitting video task ({args.model})...")
    logger.debug(f"endpoint: POST {imini.VIDEO_SUBMIT}")
    logger.debug(f"payload:\n{imini.preview_payload(payload)}")

    submitted = imini.submit(imini.VIDEO_SUBMIT, payload, api_key, logger=logger)
    task_id = submitted.get("task_id")
    if not task_id:
        logger.error(f"Submit response missing task_id: {submitted}")
        return 1

    logger.info(f"  task_id: {task_id}")
    if submitted.get("request_id"):
        logger.debug(f"  request_id: {submitted['request_id']}")

    if args.async_submit:
        print(task_id)
        return 0

    # Flat 30-minute default — covers worst-case ref-video + long-duration
    timeout = args.timeout if args.timeout is not None else imini.VIDEO_TIMEOUT_DEFAULT
    logger.info(f"→ Polling (hard timeout {int(timeout)}s, videos can take minutes)...")
    result = imini.poll(
        imini.VIDEO_QUERY,
        task_id,
        api_key,
        start_interval=5.0,
        timeout=timeout,
        logger=logger,
    )

    videos = result.get("videos") or []
    if not videos:
        logger.warn("Task succeeded but result.videos is empty.")
        return 1

    logger.info(f"✓ Generated {len(videos)} video segment(s).")

    if args.no_download:
        for i, v in enumerate(videos):
            print(f"{i}\t{v.get('url')}\t{v.get('width')}x{v.get('height')}\t{v.get('duration')}s")
        return 0

    out_paths = imini.resolve_output_paths(
        Path(args.output).expanduser() if args.output else None,
        task_id,
        len(videos),
        default_suffix=".mp4",
    )

    for v, out_path in zip(videos, out_paths):
        url = v.get("url")
        if not url:
            logger.warn(f"Video entry missing url: {v}")
            continue
        size = imini.download(url, out_path, logger=logger)
        meta = f"{v.get('width', '?')}x{v.get('height', '?')}, {v.get('duration', '?')}s"
        logger.info(f"  saved → {out_path}  ({size:,} bytes, {meta})")

    return 0


def _read_prompt(value: str) -> str:
    if value == "-":
        return sys.stdin.read()
    return value


def parse_args(argv: List[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="generate_video.py",
        description="Submit an imini video generation task and download the result.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Notes:\n"
            "  * Model IDs and field names are not hardcoded. Use --list-models to see\n"
            "    what's currently available. Use --extra '<json>' (root) or\n"
            "    --extra-params '<json>' (Kling's extra_params bag) to override.\n"
            "  * Default hard timeout is 30 minutes for all video tasks.\n"
            "    --async lets you walk away and resume with\n"
            "    poll_video_task.py --task-id <id>.\n"
            "  * IMINI_API_KEY must be set in your shell (export IMINI_API_KEY=...).\n"
        ),
    )

    p.add_argument("--list-models", action="store_true",
                   help="Print the current list of video models from llms.txt and exit.")
    p.add_argument("--refresh-cache", action="store_true",
                   help="Force a live re-fetch of llms.txt (otherwise cached for 24h).")

    p.add_argument("--model",
                   help="Model ID, e.g. kling/kling-v3, kling/kling-v3-omni, "
                        "kling/kling-v3-motion-control, doubao/seedance-2.0, "
                        "doubao/seedance-2.0-fast, dashscope/happyhorse-1.0. "
                        "Run --list-models for current list.")
    p.add_argument("--prompt", type=_read_prompt,
                   help="Text prompt. Use '-' to read from stdin. May be empty for "
                        "kling multi-shot via --extra-params.")
    p.add_argument("--output", "-o",
                   help="Output file or directory. Default: <task_id>.mp4 in cwd.")

    # Common params
    p.add_argument("--resolution",
                   help="Output resolution. Allowed values depend on model: "
                        "480P (seedance), 720P, 1080P (kling, happyhorse).")
    p.add_argument("--aspect-ratio",
                   help="Aspect ratio, e.g. 16:9, 9:16, 1:1 (model-dependent).")
    p.add_argument("--duration", type=int, metavar="SECONDS",
                   help="Video duration in seconds (model-dependent; kling: 3-15).")
    p.add_argument("--audio", action="store_true",
                   help="Enable audio generation (kling models — sets generate_audio=true).")

    # Reference media
    p.add_argument("--start-image", metavar="PATH_OR_URL",
                   help="First frame (image-to-video / first-last-frame). "
                        "Local paths auto-base64-encoded.")
    p.add_argument("--end-image", metavar="PATH_OR_URL",
                   help="Last frame (kling-v3 first-last-frame interpolation).")
    p.add_argument("--reference-image", action="append", default=[], metavar="PATH_OR_URL",
                   help="Asset reference image (repeatable). "
                        "Sets reference_type=asset on each.")
    p.add_argument("--reference-video", metavar="PATH_OR_URL",
                   help="Reference video for kling-v3-omni / seedance-2.0 / happyhorse video edit.")

    # Motion control (kling-v3-motion-control)
    p.add_argument("--character-image", metavar="PATH_OR_URL",
                   help="Character image for kling-v3-motion-control.")
    p.add_argument("--motion-video", metavar="PATH_OR_URL",
                   help="Motion source video for kling-v3-motion-control.")

    # Extras
    p.add_argument("--audio-setting", metavar="JSON_OR_STR",
                   help="happyhorse-1.0 audio config. Merged into extra_params.audio_setting.")
    p.add_argument("--extra-params", metavar="JSON",
                   help="JSON object merged into the request body's extra_params. "
                        "Use for Kling multi_shot / multi_prompt / camera_control / "
                        "negative_prompt / cfg_scale / etc.")
    p.add_argument("--extra", metavar="JSON",
                   help="JSON object merged into the request body at the root level "
                        "(escape hatch for fields this CLI doesn't expose).")

    # Behavior
    p.add_argument("--async", dest="async_submit", action="store_true",
                   help="Submit and exit, printing task_id to stdout. "
                        "Resume with poll_video_task.py --task-id <id>.")
    p.add_argument("--no-download", action="store_true",
                   help="Don't download. Print URLs to stdout instead.")
    p.add_argument("--timeout", type=float, metavar="SECONDS",
                   help="Hard timeout from submit to succeeded. Default 1800s (30 min) "
                        "for all video models. Override per-call if needed.")
    p.add_argument("--print-request", action="store_true",
                   help="Print the JSON body that would be sent and exit. Doesn't need an API key.")
    p.add_argument("--api-key", metavar="KEY",
                   help="Override $IMINI_API_KEY (DISCOURAGED — captured by shell history).")

    p.add_argument("--quiet", "-q", action="store_true", help="Suppress informational output.")
    p.add_argument("--verbose", "-v", action="store_true", help="Show detailed debug output.")

    return p.parse_args(argv)


def main(argv: List[str]) -> int:
    args = parse_args(argv)

    if args.list_models:
        return cmd_list_models(args)

    if not args.model:
        print("error: --model is required (or use --list-models to see what's available)", file=sys.stderr)
        return 2

    try:
        return cmd_generate(args)
    except imini.IminiError as e:
        print(f"\n✗ {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
