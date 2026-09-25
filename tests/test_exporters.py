from crawler.exporters import article_json, article_markdown


ARTICLE = {
    "url": "https://news.example/article",
    "title": "한국어 기사 제목",
    "publisher": "예시신문",
    "author": "홍길동 기자",
    "published_at": "2026-09-25T10:00:00+09:00",
    "article_text": "한국어 본문입니다.",
    "lead_image": "https://news.example/lead.jpg",
    "images": [{"url": "https://news.example/body.jpg", "caption": "현장 사진", "alt": "", "credit": ""}],
}


def test_json_preserves_korean_characters():
    assert "한국어 기사 제목" in article_json(ARTICLE)
    assert "\\u" not in article_json(ARTICLE)


def test_markdown_contains_attribution_and_images():
    result = article_markdown(ARTICLE)
    assert "source_url: https://news.example/article" in result
    assert "# 한국어 기사 제목" in result
    assert "![대표 이미지](https://news.example/lead.jpg)" in result
    assert "![현장 사진](https://news.example/body.jpg)" in result
