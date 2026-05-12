#!/usr/bin/env python3
"""
imini catalog fetcher and parser.

Fetches the live catalog from https://docs.imini.ai/llms.txt and parses the
"Task Query", "Image Models", and "Video Models" sections into structured
records. Uses Python stdlib only (urllib) — no `pip install` required.

Usage:
    python3 fetch_imini_catalog.py                          # list all records
    python3 fetch_imini_catalog.py --type image             # images only
    python3 fetch_imini_catalog.py --type video             # videos only
    python3 fetch_imini_catalog.py --model google/nano-banana-pro
    python3 fetch_imini_catalog.py --json                   # raw JSON output
"""

import argparse
import json
import re
import sys
import urllib.request
from typing import Dict, List, Optional

LLMS_URL = "https://docs.imini.ai/llms.txt"

LINE_RE = re.compile(
    r'^-\s+(?P<category>.+?)\s+'
    r'\[(?P<name>.+?)\]\((?P<doc_url>[^)]+)\):\s*'
    r'(?P<description>.*?)'
    r'(?:\s+Pricing[^:]*?:\s+(?P<pricing>.+?))?'
    r'(?:\s+Spec:\s+(?P<spec_url>\S+))?$'
)

MODEL_ID_RE = re.compile(r'[a-z][a-z0-9_-]*/[a-z0-9.\-]+')

API_SECTIONS = {
    "Task Query": "task-query",
    "Image Models (POST /v1/images/generate)": "image",
    "Video Models (POST /v1/videos/generate)": "video",
}


def fetch(url: str = LLMS_URL, timeout: int = 30) -> str:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "imini-skill-catalog-fetcher/0.1"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8")


def parse(content: str) -> List[Dict]:
    records: List[Dict] = []
    current_section: Optional[str] = None

    for raw_line in content.splitlines():
        line = raw_line.strip()
        if line.startswith("## "):
            current_section = line[3:].strip()
            continue
        if not line.startswith("- "):
            continue
        record_type = API_SECTIONS.get(current_section or "")
        if not record_type:
            continue

        match = LINE_RE.match(line)
        if not match:
            continue

        record = match.groupdict()
        record["section"] = current_section
        record["type"] = record_type

        model_match = MODEL_ID_RE.search(record["category"])
        record["model_id"] = model_match.group(0) if model_match else None

        records.append(record)

    return records


def filter_records(
    records: List[Dict],
    type_: Optional[str] = None,
    model: Optional[str] = None,
) -> List[Dict]:
    out = records
    if type_:
        out = [r for r in out if r.get("type") == type_]
    if model:
        out = [r for r in out if r.get("model_id") == model]
    return out


def format_human(records: List[Dict], show_pricing: bool = True) -> str:
    lines: List[str] = []
    for r in records:
        lines.append(f"[{r['type']}] {r['name']}")
        if r.get("model_id"):
            lines.append(f"  Model ID: {r['model_id']}")
        lines.append(f"  Docs:     {r['doc_url']}")
        if r.get("spec_url"):
            lines.append(f"  Spec:     {r['spec_url']}")
        lines.append(f"  Summary:  {r['description']}")
        if show_pricing and r.get("pricing"):
            lines.append(f"  Pricing:  {r['pricing']}")
        lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fetch and parse imini's llms.txt catalog.",
    )
    parser.add_argument(
        "--type",
        choices=["image", "video", "task-query"],
        help="Filter records by type.",
    )
    parser.add_argument(
        "--model",
        help="Filter to a specific model id, e.g. google/nano-banana-pro.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print JSON instead of human-readable output.",
    )
    parser.add_argument(
        "--url",
        default=LLMS_URL,
        help=f"Override the llms.txt URL (default: {LLMS_URL}).",
    )
    parser.add_argument(
        "--no-pricing",
        action="store_true",
        help="Suppress the 'Pricing' line in human output (pricing is always included in --json).",
    )
    args = parser.parse_args()

    try:
        content = fetch(args.url)
    except Exception as exc:
        print(f"Failed to fetch catalog from {args.url}: {exc}", file=sys.stderr)
        sys.exit(1)

    records = filter_records(parse(content), args.type, args.model)

    if not records:
        print("No records match the provided filters.", file=sys.stderr)
        sys.exit(2)

    if args.json:
        print(json.dumps(records, indent=2, ensure_ascii=False))
    else:
        print(format_human(records, show_pricing=not args.no_pricing))


if __name__ == "__main__":
    main()
