#!/usr/bin/env python3
"""Poll an existing imini video task by task_id and download the result.

Use this to resume from a previous --async submit, or after a timeout/network
interruption — as long as you remember the task_id.

Example:
    export IMINI_API_KEY='sk-...'
    python3 poll_video_task.py --task-id 2054220080531611649 --output ./recovered.mp4
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List

import _imini_common as imini


def parse_args(argv: List[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="poll_video_task.py",
        description="Poll an existing imini video task and (by default) download the result.",
    )
    p.add_argument("--task-id", required=True, help="Video task_id to poll.")
    p.add_argument("--output", "-o",
                   help="Output file or directory. Default: <task_id>.mp4 in cwd.")
    p.add_argument("--timeout", type=float, default=imini.VIDEO_TIMEOUT_DEFAULT,
                   metavar="SECONDS",
                   help=f"Hard timeout (default: {imini.VIDEO_TIMEOUT_DEFAULT}s = 30 min).")
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
        logger.info(f"→ Polling video task {args.task_id} (hard timeout {int(args.timeout)}s)...")

        result = imini.poll(
            imini.VIDEO_QUERY, args.task_id, api_key,
            start_interval=5.0, timeout=args.timeout, logger=logger,
        )

        videos = result.get("videos") or []
        if not videos:
            logger.warn("Task succeeded but result.videos is empty.")
            return 1

        logger.info(f"✓ Found {len(videos)} video segment(s).")

        if args.no_download:
            for i, v in enumerate(videos):
                print(f"{i}\t{v.get('url')}\t{v.get('width')}x{v.get('height')}\t{v.get('duration')}s")
            return 0

        out_paths = imini.resolve_output_paths(
            Path(args.output).expanduser() if args.output else None,
            args.task_id, len(videos),
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
    except imini.IminiError as e:
        print(f"\n✗ {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
