import json
from pathlib import Path
from zipfile import ZipFile

from renderer.hwpx.document import render
from renderer.hwpx.validator import validate


def test_creates_valid_hwpx_with_embedded_image(tmp_path):
    asset = tmp_path / "assets"; asset.mkdir()
    from PIL import Image
    Image.new("RGB", (120, 60), "blue").save(asset / "article-001-01.jpg")
    publication = {"metadata": {"issue_label": "9월 4주", "show_source_url": True}, "cover": {"year": "2026"}, "sections": [{"section_number": 1, "section_title": "정치", "articles": [{"title": "한국어 기사", "publisher": "예시신문", "author": "홍길동 기자", "published_at": "2026. 9. 25.", "source_url": "https://example.com", "body": "한국어 본문입니다.", "images": [{"local_path": "assets/article-001-01.jpg", "caption": "예시 이미지"}]}]}]}
    source = tmp_path / "publication.json"; source.write_text(json.dumps(publication, ensure_ascii=False), encoding="utf-8")
    output = render(source, tmp_path / "issue.hwpx")
    assert validate(str(output)) == []
    with ZipFile(output) as archive:
        assert archive.namelist()[0] == "mimetype"
        assert "BinData/image1.jpg" in archive.namelist()
        assert "한국어 기사" in archive.read("Contents/section0.xml").decode("utf-8")
