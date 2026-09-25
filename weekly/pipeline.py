"""Crawl -> normalized raw article -> Publication JSON. No rendering lives here."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import requests
from PIL import Image
from io import BytesIO

from crawler.extractor import extract_article
from crawler.fetcher import fetch_html
from .models import Article, Publication, Section


def _download_images(article: Article, assets: Path, article_id: int) -> None:
    records = ([{"url": article.images[0].get("url", "")}] if article.images else [])
    for image in article.images:
        if image not in records:
            records.append(image)
    for index, image in enumerate(records, 1):
        url = str(image.get("url") or "")
        if not url:
            continue
        try:
            response = requests.get(url, timeout=(5, 20), stream=True, headers={"User-Agent": "NewsCrawlerMVP/0.1"})
            response.raise_for_status()
            data = response.content
            picture = Image.open(BytesIO(data))
            picture.thumbnail((1600, 1600))
            destination = assets / f"article-{article_id:03d}-{index:02d}.jpg"
            picture.convert("RGB").save(destination, "JPEG", quality=88, optimize=True)
            image["local_path"] = str(destination.relative_to(assets.parent))
            image["width"] = str(picture.width)
            image["height"] = str(picture.height)
        except Exception as exc:
            image["download_error"] = str(exc)[:180]


def build_publication(section_specs: list[dict[str, Any]], workspace: str | Path, metadata: dict[str, Any]) -> Publication:
    root = Path(workspace)
    raw_dir, assets = root / "raw", root / "assets"
    raw_dir.mkdir(parents=True, exist_ok=True)
    assets.mkdir(parents=True, exist_ok=True)
    sections: list[Section] = []
    article_id = 0
    for spec in section_specs:
        section = Section(int(spec["section_number"]), str(spec["section_title"]))
        for url in spec["urls"]:
            article_id += 1
            page = fetch_html(str(url))
            raw = extract_article(page.url, page.text)
            raw["source_url"] = page.source_url
            (raw_dir / f"article-{article_id:03d}.json").write_text(json.dumps(raw, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            article = Article.from_crawler(raw)
            _download_images(article, assets, article_id)
            section.articles.append(article)
        sections.append(section)
    publication = Publication(metadata=metadata, cover={"year": metadata.get("year", "2026"), "subtitle": metadata.get("subtitle", "세상의 많은 이야기들")}, sections=sections)
    (root / "publication.json").write_text(json.dumps(publication.to_dict(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return publication


def load_publication(path: str | Path) -> Publication:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return Publication(metadata=data["metadata"], cover=data["cover"], sections=[Section(s["section_number"], s["section_title"], [Article(**a) for a in s["articles"]]) for s in data["sections"]])
