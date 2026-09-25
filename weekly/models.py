"""Serializable publication model: the renderer only reads this structure."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class Article:
    title: str = ""
    publisher: str = ""
    author: str = ""
    published_at: str = ""
    source_url: str = ""
    body: str = ""
    images: list[dict[str, str]] = field(default_factory=list)

    @classmethod
    def from_crawler(cls, data: dict[str, Any]) -> "Article":
        images = [item for item in data.get("images", []) if isinstance(item, dict) and item.get("url")]
        return cls(title=str(data.get("title") or ""), publisher=str(data.get("publisher") or ""), author=str(data.get("author") or ""), published_at=str(data.get("published_at") or ""), source_url=str(data.get("source_url") or data.get("url") or ""), body=str(data.get("article_text") or ""), images=[dict(item) for item in images])


@dataclass
class Section:
    section_number: int
    section_title: str
    articles: list[Article] = field(default_factory=list)


@dataclass
class Publication:
    metadata: dict[str, Any]
    cover: dict[str, Any]
    sections: list[Section] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
