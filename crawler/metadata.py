"""Metadata extraction from JSON-LD, OpenGraph, and semantic HTML."""
from __future__ import annotations

import json
import re
from typing import Any

from bs4 import BeautifulSoup

ARTICLE_TYPES = {"article", "newsarticle", "reportage", "analysisnewsarticle"}
AUTHOR_RE = re.compile(r"(?:(?P<before>[가-힣]{2,5})\s*(?:기자|특파원)|(?:기자)\s*(?P<after>[가-힣]{2,5}))")


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


def normalize_author(value: str) -> str:
    """Keep a useful byline while preventing email addresses from becoming authors."""
    value = re.sub(r"\s+", " ", value).strip()
    if not value:
        return ""
    # A byline often appends a contact address. Remove it, rather than rejecting
    # the adjacent reporter name; an address by itself still yields an empty value.
    value = re.sub(r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b", "", value).strip(" ,;|")
    if not value:
        return ""
    korean = AUTHOR_RE.search(value)
    if korean:
        name = korean.group("before") or korean.group("after")
        role = "특파원" if "특파원" in korean.group(0) else "기자"
        return f"{name} {role}"
    # Names are normally short; discard obvious prose accidentally captured from a container.
    return value if len(value) <= 100 else ""


def semantic_metadata(soup: BeautifulSoup) -> dict[str, str]:
    """Extract semantic bylines/dates without any publisher-specific selector."""
    author = ""
    for tag in soup.select("[rel='author'], [itemprop='author'], .author, .byline, .writer, .reporter"):
        author = normalize_author(tag.get("content") or tag.get_text(" ", strip=True))
        if author:
            break
    published = ""
    for tag in soup.select("time[datetime], [itemprop='datePublished'], [itemprop='dateCreated']"):
        published = (tag.get("datetime") or tag.get("content") or tag.get_text(" ", strip=True)).strip()
        if published:
            break
    h1 = soup.find("h1")
    return {
        "title": h1.get_text(" ", strip=True) if h1 else "",
        "author": author,
        "published_at": published,
    }
