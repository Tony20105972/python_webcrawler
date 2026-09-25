"""Coordinate layered article extraction without publisher-specific selectors."""
from __future__ import annotations

import re

import trafilatura
from bs4 import BeautifulSoup

from .images import absolute_url, extract_images
from .metadata import html_metadata, json_ld_article


def _fallback_text(soup: BeautifulSoup) -> str:
    candidates = soup.select("article, main, [role='main']") or [soup.body or soup]
    best = max(candidates, key=lambda tag: len(tag.get_text(" ", strip=True)))
    for unwanted in best.select("script, style, nav, footer, aside, form, figure, noscript"):
        unwanted.decompose()
    return re.sub(r"\s+", " ", best.get_text(" ", strip=True)).strip()


def extract_article(url: str, html: str) -> dict[str, object]:
    """Extract normalized article fields from already-fetched page HTML."""
    soup = BeautifulSoup(html, "html.parser")
    ld = json_ld_article(soup)
    meta = html_metadata(soup)
    extracted = trafilatura.extract(html, include_comments=False, include_tables=False) or ""

    def choose(field: str, default: str = "") -> str:
        return str(ld.get(field) or meta.get(field) or default).strip()

    lead = absolute_url(url, choose("lead_image"))
    images = extract_images(soup, url, lead)
    # Fallback removes boilerplate nodes, so collect images before it mutates the tree.
    fallback = _fallback_text(soup)
    return {
        "url": url,
        "title": choose("title"),
        "publisher": choose("publisher"),
        "author": choose("author"),
        "published_at": choose("published_at"),
        "article_text": str(ld.get("article_text") or extracted or fallback).strip(),
        "lead_image": lead or "",
        "images": images,
    }
