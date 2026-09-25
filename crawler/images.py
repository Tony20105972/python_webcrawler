"""Article-oriented image collection and URL normalization."""
from __future__ import annotations

from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup, Tag

BAD_TERMS = ("logo", "favicon", "icon", "avatar", "profile", "advert", "banner", "tracking", "pixel", "sprite", "nav", "menu")


def absolute_url(base_url: str, value: str | None) -> str | None:
    if not value:
        return None
    value = value.strip()
    if value.startswith(("data:", "javascript:", "#")):
        return None
    result = urljoin(base_url, value)
    return result if urlparse(result).scheme in {"http", "https"} else None


def _src_from_tag(tag: Tag) -> str | None:
    srcset = tag.get("srcset") or tag.get("data-srcset")
    if srcset:
        # Usually the last candidate is the largest responsive rendition.
        return srcset.split(",")[-1].strip().split()[0]
    return tag.get("src") or tag.get("data-src") or tag.get("data-original")


def _excluded(tag: Tag, url: str) -> bool:
    nearby = " ".join(
        [url, str(tag.get("alt", "")), " ".join(tag.get("class", [])), str(tag.get("id", ""))]
    ).lower()
    if any(term in nearby for term in BAD_TERMS):
        return True
    width, height = tag.get("width"), tag.get("height")
    try:
        if int(width or 999) <= 2 or int(height or 999) <= 2:
            return True
    except ValueError:
        pass
    return url.lower().split("?")[0].endswith(".svg")


def extract_images(soup: BeautifulSoup, base_url: str, lead_image: str | None = None) -> list[str]:
    """Return distinct likely editorial images, with the lead image first."""
    candidates: list[str] = []
    if lead := absolute_url(base_url, lead_image):
        candidates.append(lead)
    roots = soup.select("article, main") or [soup]
    for root in roots:
        for tag in root.find_all(["img", "source"]):
            raw = _src_from_tag(tag)
            url = absolute_url(base_url, raw)
            if url and not _excluded(tag, url):
                candidates.append(url)
    seen: set[str] = set()
    return [url for url in candidates if not (url in seen or seen.add(url))]
