"""Preflight checks for a publication and a reference-layout comparison summary."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from .models import Publication


def validate_publication(publication: Publication, workspace: str | Path | None = None) -> dict[str, Any]:
    issues: list[dict[str, str]] = []
    article_count = 0
    for section in publication.sections:
        if not section.articles:
            issues.append({"level": "warning", "message": f"주간시사 {section.section_number}: 기사가 없습니다."})
        for article in section.articles:
            article_count += 1
            label = f"기사 {article_count}"
            if not article.title: issues.append({"level": "error", "message": f"{label}: 제목 누락"})
            if not article.body: issues.append({"level": "error", "message": f"{label}: 본문 누락"})
            if len(article.body) < 200: issues.append({"level": "warning", "message": f"{label}: 본문이 200자 미만"})
            if not article.author: issues.append({"level": "warning", "message": f"{label}: 기자명 누락"})
            if not article.published_at: issues.append({"level": "warning", "message": f"{label}: 날짜 누락"})
            if not article.images: issues.append({"level": "warning", "message": f"{label}: 이미지 누락"})
            for image in article.images:
                if image.get("width") and image.get("height"):
                    ratio = int(image["width"]) / max(int(image["height"]), 1)
                    if ratio < .35 or ratio > 3.5: issues.append({"level": "warning", "message": f"{label}: 비정상 이미지 비율 {ratio:.2f}"})
                if image.get("download_error"): issues.append({"level": "warning", "message": f"{label}: 이미지 다운로드 실패"})
    return {"reference": {"expected_sections": 4, "reference_page_size": "A4", "reference_page_count": 24}, "actual": {"sections": len(publication.sections), "articles": article_count}, "issues": issues, "empty_page_risk": "low" if article_count else "high", "valid": not any(i["level"] == "error" for i in issues)}
