"""Publication JSON -> HWPX. This module intentionally has no crawler imports."""
from __future__ import annotations
import json, re
from pathlib import Path
from .image import image_paragraph
from .package import package
from .paragraph import paragraph, section_start
from .styles import BODY_CHAR, BODY_PARA, META_CHAR, META_PARA, SECTION_CHAR, SECTION_PARA, TITLE_CHAR, TITLE_PARA

SEC_PR = re.compile(r"<hp:secPr.*?</hp:secPr>", re.S)
COL_PR = re.compile(r"<hp:ctrl>.*?</hp:ctrl>", re.S)
ROOT = '<hs:sec xmlns:ha="http://www.hancom.co.kr/hwpml/2011/app" xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph" xmlns:hs="http://www.hancom.co.kr/hwpml/2011/section" xmlns:hc="http://www.hancom.co.kr/hwpml/2011/core">'

def _skeleton() -> tuple[str, str]:
    template = Path(__file__).with_name("template") / "Contents" / "section0.xml"
    source = template.read_text(encoding="utf-8")
    return SEC_PR.search(source).group(), COL_PR.search(source).group()

def render(publication_json: str | Path, output: str | Path, template_path: str | Path | None = None) -> Path:
    data = json.loads(Path(publication_json).read_text(encoding="utf-8")); root = Path(publication_json).parent
    secpr, colpr = _skeleton(); body = [section_start(secpr, colpr)]
    cover, metadata = data.get("cover", {}), data.get("metadata", {})
    body += [paragraph("카이로스(시대인재) 김윤환논술", META_CHAR, META_PARA), paragraph(f"{cover.get('year', metadata.get('year', '2026'))}학년도", TITLE_CHAR, TITLE_PARA), paragraph("시사 읽기자료집", TITLE_CHAR, TITLE_PARA), paragraph(str(cover.get('subtitle', '세상의 많은 이야기들')), META_CHAR, META_PARA), paragraph("", BODY_CHAR, BODY_PARA, page_break=True)]
    body += [paragraph("김윤환CLASS", TITLE_CHAR, TITLE_PARA), paragraph("시사 읽기자료집", TITLE_CHAR, TITLE_PARA), paragraph(str(metadata.get("issue_label", "주간시사")), META_CHAR, META_PARA)]
    embedded: list[tuple[str, Path]] = []; seen = 0
    for section in data.get("sections", []):
        body.append(paragraph(f"주간시사 {section.get('section_number')} | {section.get('section_title', '')}", SECTION_CHAR, SECTION_PARA))
        for article in section.get("articles", []):
            body.append(paragraph(article.get("title") or "제목 없음", TITLE_CHAR, TITLE_PARA))
            meta = " | ".join(v for v in [article.get("publisher", ""), article.get("author", ""), article.get("published_at", "")] if v)
            body.append(paragraph(meta, META_CHAR, META_PARA))
            if metadata.get("show_source_url", True) and article.get("source_url"): body.append(paragraph(article["source_url"], META_CHAR, META_PARA))
            for image in article.get("images", [])[:2]:
                local = image.get("local_path")
                if local and (root / local).is_file():
                    seen += 1; image_id = f"image{seen}"; path = root / local
                    embedded.append((image_id, path)); body.append(image_paragraph(image_id, path))
                    if image.get("caption") or image.get("alt"): body.append(paragraph(image.get("caption") or image.get("alt"), META_CHAR, META_PARA))
            for line in str(article.get("body") or "").splitlines():
                if line.strip(): body.append(paragraph(line.strip(), BODY_CHAR, BODY_PARA))
    xml = "<?xml version='1.0' encoding='UTF-8'?>" + ROOT + "".join(body) + "</hs:sec>"
    return package(output, xml, embedded, "주간시사 시사 읽기자료집")
