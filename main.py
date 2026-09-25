#!/usr/bin/env python3
"""CLI entry point for the news article crawler."""
from __future__ import annotations

import argparse
import sys

from crawler.exporters import article_json, article_markdown
from crawler.extractor import extract_article
from crawler.fetcher import FetchError, fetch_html


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract information from one public news article URL.")
    parser.add_argument("url", help="Public news article URL")
    parser.add_argument("--json", dest="json_path", metavar="FILE", help="Save the result as UTF-8 JSON")
    parser.add_argument("--markdown", dest="markdown_path", metavar="FILE", help="Save the result as UTF-8 Markdown")
    args = parser.parse_args()

    try:
        response = fetch_html(args.url)
        article = extract_article(response.url, response.text)
        article["source_url"] = response.source_url
    except FetchError as exc:
        print(f"Fetch failed: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:  # Keep CLI failures understandable without hiding library errors in tests.
        print(f"Extraction failed: {exc}", file=sys.stderr)
        return 3

    json_result = article_json(article)
    if args.json_path:
        with open(args.json_path, "w", encoding="utf-8") as output:
            output.write(json_result)
    if args.markdown_path:
        with open(args.markdown_path, "w", encoding="utf-8") as output:
            output.write(article_markdown(article))
    if not args.json_path:
        print(json_result, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
