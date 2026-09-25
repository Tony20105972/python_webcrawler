"""PDF renderer: consumes publication.json and the external layout template only."""
from __future__ import annotations

import json
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import BaseDocTemplate, Frame, Image, PageBreak, Paragraph, Spacer

from .models import Publication

FONT_PATH = "/System/Library/Fonts/Supplemental/AppleGothic.ttf"


def _template(path: str | Path | None) -> dict:
    default = Path(__file__).resolve().parents[1] / "templates" / "weekly_current_affairs.json"
    return json.loads(Path(path or default).read_text(encoding="utf-8"))


def render_pdf(publication: Publication, output: str | Path, workspace: str | Path, template_path: str | Path | None = None) -> Path:
    cfg, out, root = _template(template_path), Path(output), Path(workspace)
    if "Korean" not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont("Korean", FONT_PATH))
    page, colors = cfg["page"], cfg["colors"]
    left, right, top, bottom = (page["margin_left_mm"] * mm, page["margin_right_mm"] * mm, page["margin_top_mm"] * mm, page["margin_bottom_mm"] * mm)
    width, height = A4
    frame = Frame(left, bottom, width-left-right, height-top-bottom, id="body")

    def furniture(canvas, doc):
        if doc.page == 1:
            canvas.saveState()
            canvas.setFillColor(HexColor(cfg["cover"]["background"]))
            canvas.rect(0, 0, width, height, fill=1, stroke=0)
            canvas.setStrokeColor(HexColor("#F0F0F0")); canvas.setLineWidth(1)
            for y in (height-35*mm, height-80*mm, height-125*mm): canvas.line(34*mm, y, 95*mm, y)
            canvas.circle(65*mm, height-140*mm, 22*mm, stroke=1, fill=0)
            canvas.restoreState()
            return
        canvas.saveState(); canvas.setFont("Korean", cfg["header"]["font_size_pt"]); canvas.setFillColor(HexColor(colors["ink"]))
        canvas.drawString(left, height-10*mm, cfg["header"]["left_text"]); canvas.drawRightString(width-right, height-10*mm, cfg["header"]["right_text"])
        canvas.setStrokeColor(HexColor(colors["section_grey"])); canvas.line(left, height-12*mm, width-right, height-12*mm)
        canvas.setStrokeColor(HexColor(colors["rule"])); canvas.line(left, 12*mm, width-right, 12*mm)
        canvas.setFillColor(HexColor(colors["accent_blue"])); canvas.setFont("Korean", cfg["footer"]["font_size_pt"]); canvas.drawString(left, 8*mm, cfg["footer"]["url"])
        canvas.setFillColor(HexColor(colors["ink"])); canvas.drawRightString(width-right, 8*mm, str(doc.page-1)); canvas.restoreState()

    doc = BaseDocTemplate(str(out), pagesize=A4, leftMargin=left, rightMargin=right, topMargin=top, bottomMargin=bottom)
    doc.addPageTemplates([__import__('reportlab.platypus', fromlist=['PageTemplate']).PageTemplate(id="weekly", frames=[frame], onPage=furniture)])
    title = ParagraphStyle("title", fontName="Korean", fontSize=cfg["article_title"]["font_size_pt"], leading=cfg["article_title"]["leading_pt"], textColor=HexColor(colors["ink"]), spaceBefore=5*mm, spaceAfter=2*mm)
    meta = ParagraphStyle("meta", fontName="Korean", fontSize=cfg["metadata"]["font_size_pt"], leading=cfg["metadata"]["leading_pt"], textColor=HexColor(colors["ink"]), spaceAfter=4*mm)
    body = ParagraphStyle("body", fontName="Korean", fontSize=cfg["body"]["font_size_pt"], leading=cfg["body"]["leading_pt"], alignment=4, spaceAfter=cfg["body"]["paragraph_spacing_pt"], textColor=HexColor(colors["ink"]))
    story = []
    cover = cfg["cover"]
    story += [Spacer(1, 35*mm), Paragraph(f"<font size=\"11\">{escape(cover['brand_korean'])}</font><br/><font size=\"15\">{escape(str(publication.cover.get('year', '2026')))}{cover['year_suffix']}</font>", meta), Spacer(1, 45*mm), Paragraph(f"<font size=\"30\"><b>{cover['title']}</b></font><br/>{escape(str(publication.cover.get('subtitle', cover['subtitle'])))}", ParagraphStyle("cover", parent=meta, leading=38, fontSize=12)), Spacer(1, 50*mm), Paragraph(cover['brand'], ParagraphStyle("brand", parent=meta, alignment=2, fontSize=9)), PageBreak()]
    story += [Paragraph(f"<font size=\"18\"><b>{cfg['intro']['class_label']}<br/>{cfg['intro']['title']}</b></font>", meta), Paragraph(escape(str(publication.metadata.get('issue_label', '주간시사'))), meta), Spacer(1, 8*mm)]
    for section in publication.sections:
        story += [Paragraph(f"<font color=\"white\"><b>{cfg['section']['label_prefix']} {section.section_number} | {escape(section.section_title)}</b></font>", ParagraphStyle("section", parent=meta, backColor=HexColor(colors['section_grey']), borderPadding=5, spaceBefore=7*mm, spaceAfter=5*mm))]
        for article in section.articles:
            story.append(Paragraph(escape(article.title or "제목 없음"), title))
            story.append(Paragraph(escape(" | ".join(x for x in [article.publisher, article.author, article.published_at] if x) + ("<br/>" + article.source_url if article.source_url else "")), meta))
            for image in article.images[:2]:
                local = image.get("local_path")
                if local and (root / local).exists():
                    picture = Image(str(root / local)); picture._restrictSize(cfg['image']['max_width_mm']*mm, cfg['image']['max_height_mm']*mm)
                    story.extend([picture, Paragraph(escape(image.get('caption') or image.get('alt') or ""), ParagraphStyle("caption", parent=meta, fontSize=6.5, leading=8)), Spacer(1, 2*mm)])
            for paragraph in article.body.splitlines():
                if paragraph.strip(): story.append(Paragraph(escape(paragraph.strip()), body))
    doc.build(story)
    return out
