"""Metadata extraction from JSON-LD, OpenGraph, and semantic HTML."""
from __future__ import annotations

import json
from typing import Any

from bs4 import BeautifulSoup

ARTICLE_TYPES = {"article", "newsarticle", "reportage", "analysisnewsarticle"}


def text_value(value: Any) -> str | None:
    if isinstance(value, str):
        return value.strip() or None
    if isinstance(value, dict):
        return text_value(value.get("name") or value.get("@id"))
    if isinstance(value, list):
        values = [text_value(item) for item in value]
        return ", ".join(item for item in values if item) or None
    return None


def image_value(value: Any) -> str | None:
    if isinstance(value, list):
        for item in value:
            found = image_value(item)
            if found:
                return found
    if isinstance(value, dict):
        return image_value(value.get("url") or value.get("contentUrl") or value.get("@id"))
    return text_value(value)


def _nodes(value: Any):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _nodes(child)
    elif isinstance(value, list):
        for child in value:
            yield from _nodes(child)


def json_ld_article(soup: BeautifulSoup) -> dict[str, str]:
    """Return first article-shaped JSON-LD item, including common nested graphs."""
    for script in soup.select('script[type="application/ld+json"]'):
        raw = script.string or script.get_text()
        try:
            data = json.loads(raw.strip())
        except (json.JSONDecodeError, AttributeError):
            continue
        for node in _nodes(data):
            kinds = node.get("@type", [])
            kinds = [kinds] if isinstance(kinds, str) else kinds
            if not any(str(kind).lower() in ARTICLE_TYPES for kind in kinds):
                continue
            return {
                "title": text_value(node.get("headline") or node.get("name")) or "",
                "publisher": text_value(node.get("publisher")) or "",
                "author": text_value(node.get("author")) or "",
                "published_at": text_value(node.get("datePublished")) or "",
                "lead_image": image_value(node.get("image")) or "",
                "article_text": text_value(node.get("articleBody")) or "",
            }
    return {}


def _meta(soup: BeautifulSoup, *names: str) -> str | None:
    wanted = {name.lower() for name in names}
    for tag in soup.find_all("meta"):
        key = (tag.get("property") or tag.get("name") or tag.get("itemprop") or "").lower()
        if key in wanted:
            value = tag.get("content")
            if value and value.strip():
                return value.strip()
    return None


def html_metadata(soup: BeautifulSoup) -> dict[str, str]:
    title_tag = soup.find("title")
    h1 = soup.find("h1")
    publisher = _meta(soup, "og:site_name", "application-name", "publisher")
    return {
        "title": _meta(soup, "og:title", "twitter:title", "headline") or (h1.get_text(" ", strip=True) if h1 else "") or (title_tag.get_text(" ", strip=True) if title_tag else ""),
        "publisher": publisher or "",
        "author": _meta(soup, "author", "article:author") or "",
        "published_at": _meta(soup, "article:published_time", "datepublished", "date") or "",
        "lead_image": _meta(soup, "og:image", "og:image:url", "twitter:image", "image") or "",
        "description": _meta(soup, "description", "og:description") or "",
    }
