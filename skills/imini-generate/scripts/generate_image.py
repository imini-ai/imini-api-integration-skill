#!/usr/bin/env python3
"""Submit and (by default) poll an imini image generation task.

Stdlib only (Python 3.8+). No model IDs or per-model field lists are
hardcoded — passing `--list-models` reads from llms.txt (live, with 24h
cache fallback). For any field this CLI doesn't surface explicitly, use
`--extra '<json>'` to merge it into the request body.

Example:
    export IMINI_API_KEY='sk-...'
    python3 generate_image.py \\
        --model google/nano-banana-pro \\
        --prompt "a moody cinematic portrait at golden hour" \\
        --resolution 4K --aspect-ratio 16:9 \\
        --output ./out.png
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

import _imini_common as imini


def build_payload(args: argparse.Namespace) -> Dict[str, Any]:
    """Translate CLI flags into the JSON body for POST /v1/images/generate.

    No per-model branching — the same flag names map to consistent JSON keys
    documented in the OpenAPI specs at https://docs.imini.ai/en/openapi/images/.
    Pass `--extra '{...}'` (root-level merge) to override anything.
    """
    payload: Dict[str, Any] = {"model": args.model}

    if args.prompt is not None:
        payload["prompt"] = args.prompt

    if args.resolution:
        payload["resolution"] = args.resolution

    if args.aspect_ratio:
        payload["aspect_ratio"] = args.aspect_ratio

    if args.num_images is not None:
        # Some models accept `n`, others might accept `num_images`. nano-banana family
        # uses `n` per published examples. Override with --extra if your model differs.
        payload["n"] = args.num_images

    if args.quality:
        # openai/gpt-image-2 uses `quality` (low/medium/high).
        payload["quality"] = args.quality

    # Reference images: build `images: [{url, reference_type}]`
    images: List[Dict[str, str]] = []
    for path in (args.reference_image or []):
        images.append({"url": imini.as_url(path), "reference_type": "asset"})
    for path in (args.style_reference or []):
        images.append({"url": imini.as_url(path), "reference_type": "style"})
    if images:
        payload["images"] = images

    # Escape hatch: arbitrary root-level merge
    payload.update(imini.parse_json_arg(args.extra, flag_name="--extra"))

    return payload


def cmd_list_models(args: argparse.Namespace) -> int:
    logger = imini.Logger(quiet=args.quiet, verbose=args.verbose)
    content = imini.fetch_catalog(refresh=args.refresh_cache, logger=logger)
    models = imini.parse_models(content, type_filter="image")
    if not models:
        logger.error("No image models found in catalog.")
        return 2
    print(f"Image models available on imini (catalog from {imini.LLMS_URL}):\n")
    print(imini.format_model_list(models))
    return 0


def cmd_generate(args: argparse.Namespace) -> int:
    logger = imini.Logger(quiet=args.quiet, verbose=args.verbose)

    # Build payload first so --print-request can short-circuit without auth
    payload = build_payload(args)

    if args.print_request:
        print(imini.preview_payload(payload))
        return 0

    if args.prompt is None:
        logger.error("--prompt is required (use --prompt - to read from stdin).")
        return 2

    api_key = imini.resolve_api_key(args.api_key, logger=logger)

    logger.info(f"→ Submitting image task ({args.model})...")
    logger.debug(f"endpoint: POST {imini.IMAGE_SUBMIT}")
    logger.debug(f"payload:\n{imini.preview_payload(payload)}")

    submitted = imini.submit(imini.IMAGE_SUBMIT, payload, api_key, logger=logger)
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

    # Poll until terminal — flat 10-minute default
    timeout = args.timeout if args.timeout is not None else imini.IMAGE_TIMEOUT_DEFAULT
    logger.info(f"→ Polling (hard timeout {int(timeout)}s)...")
    result = imini.poll(
        imini.IMAGE_QUERY,
        task_id,
        api_key,
        start_interval=2.0,
        timeout=timeout,
        logger=logger,
    )

    images = result.get("images") or []
    if not images:
        logger.warn("Task succeeded but result.images is empty.")
        return 1

    logger.info(f"✓ Generated {len(images)} image(s).")

    if args.no_download:
        for i, img in enumerate(images):
            print(f"{i}\t{img.get('url')}\t{img.get('width')}x{img.get('height')}")
        return 0

    out_paths = imini.resolve_output_paths(
        Path(args.output).expanduser() if args.output else None,
        task_id,
        len(images),
        default_suffix=".png",
    )

    for img, out_path in zip(images, out_paths):
        url = img.get("url")
        if not url:
            logger.warn(f"Image entry missing url: {img}")
            continue
        size = imini.download(url, out_path, logger=logger)
        meta = f"{img.get('width', '?')}x{img.get('height', '?')}"
        logger.info(f"  saved → {out_path}  ({size:,} bytes, {meta})")

    return 0


def _read_prompt(value: str) -> str:
    if value == "-":
        return sys.stdin.read()
    return value


def parse_args(argv: List[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="generate_image.py",
        description="Submit an imini image generation task and download the result.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Notes:\n"
            "  * Model IDs and field names are not hardcoded. Use --list-models to see\n"
            "    what's currently available, and --extra '<json>' to send fields this\n"
            "    CLI doesn't expose directly.\n"
            "  * IMINI_API_KEY must be set in your shell (export IMINI_API_KEY=...).\n"
            "    Don't paste keys into chat or pass via --api-key in shared shells.\n"
        ),
    )

    p.add_argument("--list-models", action="store_true",
                   help="Print the current list of image models from llms.txt and exit.")
    p.add_argument("--refresh-cache", action="store_true",
                   help="Force a live re-fetch of llms.txt (otherwise cached for 24h).")

    p.add_argument("--model",
                   help="Model ID, e.g. google/nano-banana, google/nano-banana-pro, "
                        "google/nano-banana-2, openai/gpt-image-2. Run --list-models for current list.")
    p.add_argument("--prompt", type=_read_prompt,
                   help="Text prompt. Use '-' to read from stdin (heredoc-friendly).")
    p.add_argument("--output", "-o",
                   help="Output file or directory. Default: <task_id>.png in cwd. "
                        "When multiple images come back, '-0' / '-1' / ... is inserted before suffix.")

    # Common image params
    p.add_argument("--resolution",
                   help="Resolution tier. Common values: 512 / 1K / 2K / 4K. "
                        "Allowed values depend on the model.")
    p.add_argument("--aspect-ratio",
                   help="Aspect ratio, e.g. 1:1, 16:9, 9:16, 4:3, 21:9 (model-dependent).")
    p.add_argument("--num-images", type=int,
                   help="Number of images to generate (sent as 'n'). Model-dependent.")
    p.add_argument("--quality",
                   help="Quality tier (low / medium / high). Used by openai/gpt-image-2.")

    # Reference images
    p.add_argument("--reference-image", action="append", default=[], metavar="PATH_OR_URL",
                   help="Reference image (repeatable). Local paths are auto-base64-encoded "
                        "into a data: URL. URLs are passed through. Sets reference_type=asset.")
    p.add_argument("--style-reference", action="append", default=[], metavar="PATH_OR_URL",
                   help="Style reference image (repeatable). Same as --reference-image but "
                        "sets reference_type=style (e.g. nano-banana-pro style transfer).")

    # Escape hatch
    p.add_argument("--extra", metavar="JSON",
                   help="JSON object merged into the request body at the root level. "
                        "Use this for fields this CLI doesn't expose, or for model-specific "
                        "fields. Example: --extra '{\"some_new_field\": \"value\"}'")

    # Behavior
    p.add_argument("--async", dest="async_submit", action="store_true",
                   help="Submit and exit, printing task_id to stdout. "
                        "Resume with poll_image_task.py --task-id <id>.")
    p.add_argument("--no-download", action="store_true",
                   help="Don't download result files. Print URLs to stdout instead.")
    p.add_argument("--timeout", type=float, metavar="SECONDS",
                   help="Hard timeout from submit to succeeded. Default 600s (10 min) "
                        "for all image models. Override per-call if needed.")
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
