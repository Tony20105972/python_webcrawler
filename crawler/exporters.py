"""UTF-8-safe export helpers shared by the CLI and Streamlit app."""
from __future__ import annotations

import json
from typing import Any


def article_json(article: dict[str, Any]) -> str:
    """Serialize an article without escaping Korean or other Unicode text."""
    return json.dumps(article, ensure_ascii=False, indent=2) + "\n"


def _value(article: dict[str, Any], key: str) -> str:
    return str(article.get(key) or "")


def article_markdown(article: dict[str, Any]) -> str:
    """Create a portable Markdown document while preserving source attribution."""
    title = _value(article, "title") or "제목 없음"
    publisher = _value(article, "publisher") or "출처 미상"
    author = _value(article, "author") or "기자 미상"
    published_at = _value(article, "published_at") or "날짜 미상"
    source_url = _value(article, "source_url") or _value(article, "url")
    lines = [
        "---",
        f"title: {title}",
        f"publisher: {publisher}",
        f"author: {author}",
        f"published_at: {published_at}",
        f"source_url: {source_url}",
        "---",
        "",
        f"# {title}",
        "",
        f"{publisher} | {author} | {published_at}",
        "",
    ]
    lead_image = _value(article, "lead_image")
    if lead_image:
        lines.extend(["![대표 이미지](%s)" % lead_image, ""])
    lines.extend(["## 본문", "", _value(article, "article_text"), "", "## 이미지", ""])
    for image in article.get("images", []):
        if not isinstance(image, dict) or not image.get("url"):
            continue
        caption = str(image.get("caption") or image.get("alt") or "이미지")
        lines.extend([f"![{caption}]({image['url']})", "", caption, ""])
    return "\n".join(lines).rstrip() + "\n"
