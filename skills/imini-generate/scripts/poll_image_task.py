#!/usr/bin/env python3
"""Poll an existing imini image task by task_id and download the result.

Use this to resume from a previous --async submit, or after a timeout/network
interruption — as long as you remember the task_id.

Example:
    export IMINI_API_KEY='sk-...'
    python3 poll_image_task.py --task-id 2054220080531611648 --output ./recovered.png
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List

import _imini_common as imini


def parse_args(argv: List[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="poll_image_task.py",
        description="Poll an existing imini image task and (by default) download the result.",
    )
    p.add_argument("--task-id", required=True, help="Image task_id to poll.")
    p.add_argument("--output", "-o",
                   help="Output file or directory. Default: <task_id>.png in cwd.")
    p.add_argument("--timeout", type=float, default=imini.IMAGE_TIMEOUT_DEFAULT,
                   metavar="SECONDS",
                   help=f"Hard timeout (default: {imini.IMAGE_TIMEOUT_DEFAULT}s = 10 min).")
    p.add_argument("--no-download", action="store_true",
                   help="Don't download. Print URLs to stdout instead.")
    p.add_argument("--api-key", help="Override $IMINI_API_KEY (DISCOURAGED).")
    p.add_argument("--quiet", "-q", action="store_true", help="Suppress informational output.")
    p.add_argument("--verbose", "-v", action="store_true", help="Show detailed debug output.")
    return p.parse_args(argv)


def main(argv: List[str]) -> int:
    args = parse_args(argv)
    logger = imini.Logger(quiet=args.quiet, verbose=args.verbose)

    try:
        api_key = imini.resolve_api_key(args.api_key, logger=logger)
        logger.info(f"→ Polling image task {args.task_id} (hard timeout {int(args.timeout)}s)...")

        result = imini.poll(
            imini.IMAGE_QUERY, args.task_id, api_key,
            start_interval=2.0, timeout=args.timeout, logger=logger,
        )

        images = result.get("images") or []
        if not images:
            logger.warn("Task succeeded but result.images is empty.")
            return 1

        logger.info(f"✓ Found {len(images)} image(s).")

        if args.no_download:
            for i, img in enumerate(images):
                print(f"{i}\t{img.get('url')}\t{img.get('width')}x{img.get('height')}")
            return 0

        out_paths = imini.resolve_output_paths(
            Path(args.output).expanduser() if args.output else None,
            args.task_id, len(images),
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
    except imini.IminiError as e:
        print(f"\n✗ {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
