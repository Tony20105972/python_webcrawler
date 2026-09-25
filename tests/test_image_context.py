from bs4 import BeautifulSoup
from crawler.images import extract_images


def urls(html: str):
    return [x["url"] for x in extract_images(BeautifulSoup(html, "html.parser"), "https://news.example/story")]


def test_figure_kept_and_related_card_excluded():
    html = """<article><p>충분히 긴 본문 문단입니다. 기사 내용이 여기 계속 이어집니다.</p><figure><img src='/a.jpg'><figcaption>현장 사진</figcaption></figure><p>다음 기사 본문 문단도 충분히 깁니다.</p><section class='related-news'><a href='/other'><img src='/b.jpg'><h3>다른 기사 제목</h3></a></section></article>"""
    assert urls(html) == ["https://news.example/a.jpg"]


def test_lead_and_inline_body_image_kept_popular_excluded():
    html = """<article><img src='/a.jpg'><p>충분한 기사 본문 내용입니다. 계속되는 문장입니다.</p><img data-src='/b.jpg'><p>본문이 이어집니다. 충분히 긴 문장입니다.</p><div class='popular-news'><img src='/c.jpg'><img src='/d.jpg'></div></article>"""
    assert urls(html) == ["https://news.example/a.jpg", "https://news.example/b.jpg"]


def test_inline_related_card_is_excluded_but_following_figure_is_kept():
    html = """<article><p>첫 본문 문단은 충분히 길게 작성합니다. 중요한 기사 내용입니다.</p><div class='recommend card'><a href='/another'><img src='/x.jpg'><h3>다른 기사 제목</h3></a></div><figure><img src='/y.jpg'><figcaption>기사 사진</figcaption></figure><p>마지막 본문 문단도 충분히 깁니다.</p></article>"""
    assert urls(html) == ["https://news.example/y.jpg"]


def test_picture_lazy_srcset_and_caption():
    html = """<article><p>본문 문단이 충분히 길어서 문맥 검사를 통과합니다. 기사 내용입니다.</p><figure><picture><source srcset='/small.jpg 400w, /large.jpg 1600w'><img data-src='/fallback.jpg'></picture><figcaption>서울 현장 <span class='credit'>연합뉴스</span></figcaption></figure><p>다음 본문 문단도 충분한 길이입니다.</p></article>"""
    images = extract_images(BeautifulSoup(html, "html.parser"), "https://news.example/story")
    assert len(images) == 1
    assert images[0]["url"] == "https://news.example/large.jpg"
    assert images[0]["caption"] == "서울 현장 연합뉴스"
