import pytest

from crawler.extractor import extract_article
from crawler.metadata import normalize_author


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("홍길동 기자", "홍길동 기자"),
        ("홍길동기자", "홍길동 기자"),
        ("기자 홍길동", "홍길동 기자"),
        ("홍길동 특파원", "홍길동 특파원"),
        ("reporter@example.com", ""),
    ],
)
def test_korean_author_normalization(raw, expected):
    assert normalize_author(raw) == expected


def test_korean_byline_noise_and_figure_metadata():
    html = """
    <html><head><meta property='og:title' content='한국 기사'><meta property='article:published_time' content='2026-09-25T10:00:00+09:00'></head>
    <body><article><div class='byline'>홍길동기자 hong@example.com</div>
    <p>첫 번째 실제 기사 문장입니다. 충분한 길이를 갖도록 내용을 작성합니다.</p>
    <p>두 번째 실제 기사 문장입니다. 독자가 읽어야 할 중요한 기사 본문입니다.</p>
    <section class='related-news'><p>관련기사: 제거되어야 합니다.</p></section>
    <figure><img data-original='/photos/a.jpg' alt='현장 사진'><figcaption>현장 모습 <span class='credit'>연합뉴스</span></figcaption></figure>
    <img srcset='/photos/s.jpg 400w, /photos/l.jpg 1200w' alt='큰 사진'><img src='/logo.svg'></article></body></html>
    """
    result = extract_article("https://news.example/item", html)
    assert result["author"] == "홍길동 기자"
    assert "관련기사" not in result["article_text"]
    assert result["images"][0] == {"url": "https://news.example/photos/a.jpg", "caption": "현장 모습 연합뉴스", "alt": "현장 사진", "credit": "연합뉴스"}
    assert result["images"][1]["url"] == "https://news.example/photos/l.jpg"
    assert result["quality"]["date"] is True


def test_quality_warns_for_missing_title_and_short_body():
    result = extract_article("https://example.test/a", "<html><body><article><p>짧음</p></article></body></html>")
    assert result["quality"]["score"] < 0.5
    assert len(result["quality"]["warnings"]) == 2
