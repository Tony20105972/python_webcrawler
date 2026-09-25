"""Coordinate layered article extraction without publisher-specific selectors."""
from __future__ import annotations

import re
from copy import copy

import trafilatura
from bs4 import BeautifulSoup

from .images import absolute_url, extract_images
from .metadata import html_metadata, json_ld_article, normalize_author, semantic_metadata

NOISE_RE = re.compile(
    r"(?:menu|navigation|advert|promo|related|popular|recommend|comment|share|social|subscribe|copyright|footer|"
    r"메뉴|네비게이션|광고|관련기사|인기기사|추천기사|댓글|공유|구독|저작권|기자프로필)",
    re.IGNORECASE,
)


def _clean_container(container) -> str:
    """Remove clearly labelled boilerplate while preserving ordinary paragraphs."""
    container = copy(container)
    for unwanted in container.select("script, style, nav, footer, aside, form, noscript"):
        unwanted.decompose()
    for tag in container.find_all(["section", "div", "ul", "ol"]):
        # A parent may already have been decomposed earlier in this iteration.
        if tag.attrs is None:
            continue
        classes = tag.get("class") or []
        marker = " ".join([str(tag.get("id", "")), " ".join(classes), str(tag.get("aria-label", ""))])
        if NOISE_RE.search(marker):
            tag.decompose()
    text = "\n".join(part.get_text(" ", strip=True) for part in container.find_all("p") if part.get_text(" ", strip=True))
    return re.sub(r"[ \t]+", " ", text).strip()


def _semantic_text(soup: BeautifulSoup) -> str:
    """Use article/main semantic regions before generic content extraction."""
    candidates = soup.select("article, main, [role='main'], [itemprop='articleBody']")
    texts = [_clean_container(candidate) for candidate in candidates]
    return max(texts, key=len, default="")


def detect_body_container(soup: BeautifulSoup):
    """Select one body node once; text and image extraction share this decision."""
    selectors = "[itemprop='articleBody'], #articleBody, #article-view-content-div, .article-body, .article_view, .article-view, .newsct_article, article, main, [role='main']"
    candidates = soup.select(selectors)
    if not candidates:
        return soup.body or soup
    def score(node) -> int:
        marker = " ".join([str(node.get("id", "")), " ".join(node.get("class", []))]).lower()
        text = sum(len(p.get_text(" ", strip=True)) for p in node.find_all("p"))
        return text + (1000 if "articlebody" in marker.replace("-", "").replace("_", "") else 0) - (10000 if NOISE_RE.search(marker) else 0)
    return max(candidates, key=score)


def _fallback_text(soup: BeautifulSoup) -> str:
    candidates = soup.select("article, main, [role='main']") or [soup.body or soup]
    best = max(candidates, key=lambda tag: len(tag.get_text(" ", strip=True)))
    for unwanted in best.select("script, style, nav, footer, aside, form, figure, noscript"):
        unwanted.decompose()
    return re.sub(r"\s+", " ", best.get_text(" ", strip=True)).strip()


def _normalized_text(value: str) -> str:
    lines = [re.sub(r"\s+", " ", line).strip() for line in value.splitlines()]
    # Conservative line-based removal only for unmistakable standalone boilerplate.
    lines = [line for line in lines if line and not (NOISE_RE.search(line) and len(line) < 100)]
    return "\n".join(lines).strip()


def _quality(article: dict[str, object]) -> dict[str, object]:
    length = len(str(article["article_text"]))
    image_count = len(article["images"])  # type: ignore[arg-type]
    title, author, date = bool(article["title"]), bool(article["author"]), bool(article["published_at"])
    score = 0.20 * title + 0.15 * author + 0.15 * date + 0.35 * min(length / 1200, 1) + 0.15 * min(image_count / 3, 1)
    warnings = []
    if not title:
        warnings.append("Title was not extracted.")
    if length < 200:
        warnings.append("Article body is unusually short.")
    return {"title": title, "author": author, "date": date, "body_length": length, "image_count": image_count, "score": round(score, 2), "warnings": warnings}


def extract_article(url: str, html: str, image_debug: bool = False) -> dict[str, object]:
    """Extract normalized article fields from already-fetched page HTML."""
    soup = BeautifulSoup(html, "html.parser")
    ld = json_ld_article(soup)
    meta = html_metadata(soup)
    semantic = semantic_metadata(soup)
    body_container = detect_body_container(soup)
    semantic_body = _semantic_text(soup)
    extracted = trafilatura.extract(html, include_comments=False, include_tables=False) or ""

    def choose(field: str, default: str = "") -> str:
        return str(ld.get(field) or meta.get(field) or semantic.get(field) or default).strip()

    lead = absolute_url(url, choose("lead_image"))
    result = extract_images(soup, url, lead, body_container=body_container, debug=image_debug)
    images, image_decisions = result if image_debug else (result, [])
    # Prefer a real body image as lead; metadata image remains a safe fallback.
    if images:
        lead = str(images[0]["url"])
    # Fallback removes boilerplate nodes, so collect images before it mutates the tree.
    fallback = _fallback_text(soup)
    # JSON-LD is authoritative; otherwise prefer a substantial semantic region, then trafilatura.
    body = str(ld.get("article_text") or (semantic_body if len(semantic_body) >= 80 else extracted) or semantic_body or fallback)
    article: dict[str, object] = {
        "url": url,
        "title": choose("title"),
        "publisher": choose("publisher"),
        "author": normalize_author(choose("author")),
        "published_at": choose("published_at"),
        "article_text": _normalized_text(body),
        "lead_image": lead or "",
        "images": images,
    }
    article["quality"] = _quality(article)
    if image_debug:
        article["image_debug"] = image_decisions
    return article
