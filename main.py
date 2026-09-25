#!/usr/bin/env python3
"""CLI entry point for the news article crawler."""
from __future__ import annotations

import argparse
import json
import sys

from crawler.extractor import extract_article
from crawler.fetcher import FetchError, fetch_html


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract information from one news article URL.")
    parser.add_argument("url", help="Public news article URL")
    args = parser.parse_args()

    try:
        response = fetch_html(args.url)
        article = extract_article(response.url, response.text)
    except FetchError as exc:
        print(f"Fetch failed: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:  # Keep CLI failures understandable without hiding library errors in tests.
        print(f"Extraction failed: {exc}", file=sys.stderr)
        return 3

    print(json.dumps(article, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
