"""A small local Streamlit application for extracting one public news article."""
from __future__ import annotations

from urllib.parse import urlparse

import streamlit as st

from crawler.exporters import article_json, article_markdown
from crawler.extractor import extract_article
from crawler.fetcher import FetchError, UnsafeUrlError, fetch_html

st.set_page_config(page_title="뉴스 기사 크롤러", page_icon="📰", layout="centered")


def is_http_url(value: str) -> bool:
    parsed = urlparse(value.strip())
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


@st.cache_data(ttl=600, show_spinner=False)
def crawl_article(url: str) -> dict[str, object]:
    """Cache completed extractions for ten minutes to avoid repeat requests."""
    page = fetch_html(url)
    article = extract_article(page.url, page.text)
    article["source_url"] = page.source_url
    return article


def show_article(article: dict[str, object]) -> None:
    st.divider()
    st.subheader(str(article.get("title") or "제목을 찾지 못했습니다"))
    st.write(f"**언론사:** {article.get('publisher') or '정보 없음'}")
    st.write(f"**기자:** {article.get('author') or '정보 없음'}")
    st.write(f"**작성일:** {article.get('published_at') or '정보 없음'}")
    st.caption(f"원본 URL: {article.get('source_url') or article.get('url')}")

    lead_image = article.get("lead_image")
    if lead_image:
        st.markdown("#### 대표 이미지")
        st.image(str(lead_image), use_container_width=True)

    st.markdown("#### 본문")
    st.write(str(article.get("article_text") or "본문을 찾지 못했습니다."))

    images = article.get("images") or []
    body_images = [image for image in images if isinstance(image, dict) and image.get("url") != lead_image]
    if body_images:
        st.markdown("#### 본문 이미지")
        for image in body_images:
            st.image(str(image["url"]), caption=str(image.get("caption") or image.get("alt") or ""), use_container_width=True)

    left, right = st.columns(2)
    safe_name = "article"
    with left:
        st.download_button("JSON 다운로드", article_json(article), f"{safe_name}.json", "application/json", use_container_width=True)
    with right:
        st.download_button("Markdown 다운로드", article_markdown(article), f"{safe_name}.md", "text/markdown", use_container_width=True)


st.title("뉴스 기사 크롤러")
st.caption("공개 기사 한 건을 분석합니다. 로그인·유료벽·CAPTCHA·robots 제한은 우회하지 않습니다.")
url = st.text_input("기사 URL", placeholder="https://news.example.com/article")

if st.button("크롤링", type="primary", use_container_width=True):
    clean_url = url.strip()
    if not is_http_url(clean_url):
        st.error("http:// 또는 https://로 시작하는 올바른 기사 URL을 입력해 주세요.")
    else:
        try:
            with st.spinner("기사를 가져와 분석하고 있습니다..."):
                st.session_state.article = crawl_article(clean_url)
            st.success("기사 분석이 완료되었습니다.")
        except UnsafeUrlError:
            st.error("로컬 또는 사설 네트워크 주소에는 접근할 수 없습니다.")
        except FetchError as exc:
            st.error(f"기사를 불러오지 못했습니다. URL, 공개 접근 여부와 네트워크를 확인해 주세요. ({exc})")
        except Exception:
            st.error("기사 분석 중 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.")

if article := st.session_state.get("article"):
    show_article(article)
