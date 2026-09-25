"""A small local Streamlit application for extracting one public news article."""
from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse
from datetime import date, timedelta

import streamlit as st

from crawler.exporters import article_json, article_markdown
from crawler.extractor import extract_article
from crawler.fetcher import FetchError, UnsafeUrlError, fetch_html
from weekly.input_parser import parse_sections
from weekly.pipeline import build_publication
from weekly.renderer import render_pdf
from weekly.validate import validate_publication
from renderer.hwpx.document import render as render_hwpx
from renderer.hwpx.validator import validate as validate_hwpx
from discovery.providers.search import GoogleNewsRssProvider
from discovery.providers.direct_rss import DirectPublisherRssProvider
from discovery.providers.composite import CompositeNewsSearchProvider
from discovery.service import discover

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

st.divider()
st.subheader("주간시사 편집 엔진")
st.caption("섹션별 URL을 수집해 `publication.json`을 만들고, 레퍼런스 레이아웃 기반 PDF로 편집합니다.")
weekly_input = st.text_area("주간시사 구성", placeholder="주간시사 1\n주제: 정치\nhttps://news.example.com/a\n\n주간시사 2\n주제: 경제\nhttps://news.example.com/b", height=220)
workspace_name = st.text_input("워크스페이스 폴더명", value="issue-2026-09-week3")
if st.button("주간시사 PDF 생성", use_container_width=True):
    try:
        specs = parse_sections(weekly_input)
        workspace = Path("workspace") / Path(workspace_name).name
        with st.spinner("기사와 이미지를 수집하고 PDF를 편집하고 있습니다..."):
            publication = build_publication(specs, workspace, {"issue_label": "주간시사", "year": "2026", "show_source_url": True})
            report = validate_publication(publication, workspace)
            pdf_path = render_pdf(publication, workspace / "weekly-current-affairs.pdf", workspace)
            hwpx_path = render_hwpx(workspace / "publication.json", workspace / "weekly-current-affairs.hwpx")
            if hwpx_errors := validate_hwpx(str(hwpx_path), str(workspace / "publication.json")):
                raise RuntimeError("HWPX package validation failed: " + "; ".join(hwpx_errors))
        st.session_state.weekly_pdf = pdf_path.read_bytes()
        st.session_state.weekly_hwpx = hwpx_path.read_bytes()
        st.session_state.weekly_report = report
        st.success(f"생성 완료: {workspace}")
    except (ValueError, FetchError, UnsafeUrlError) as exc:
        st.error(f"주간시사 생성 실패: {exc}")
    except Exception:
        st.error("문서 생성 중 오류가 발생했습니다. URL과 네트워크 상태를 확인해 주세요.")
if pdf := st.session_state.get("weekly_pdf"):
    st.download_button("주간시사 PDF 다운로드", pdf, "weekly-current-affairs.pdf", "application/pdf", use_container_width=True)
    st.download_button("주간시사 HWPX 다운로드", st.session_state.get("weekly_hwpx"), "weekly-current-affairs.hwpx", "application/hwp+zip", use_container_width=True)
    st.json(st.session_state.get("weekly_report", {}))

st.divider()
st.subheader("이번 주 기사 찾기")
start_date, end_date = st.date_input("검색 날짜 범위", value=(date.today() - timedelta(days=6), date.today()), max_value=date.today())
if st.button("후보 기사 찾기", use_container_width=True):
    try:
        with st.status("공개 뉴스 검색과 미리보기 분석 중...", expanded=True) as status:
            st.write("정치·경제·사회 검색 결과를 수집합니다.")
            issues, failures, diagnostics = discover(CompositeNewsSearchProvider([DirectPublisherRssProvider(), GoogleNewsRssProvider()]), start_date, end_date)
            st.write("본문 길이·본문 이미지·추출 품질을 사전 평가했습니다.")
            st.session_state.discovery_result = issues
            st.session_state.discovery_failures = failures
            st.session_state.discovery_diagnostics = diagnostics
            st.session_state.selected_articles = []
            status.update(label=f"이슈 {len(issues)}개 발견", state="complete")
    except Exception as exc:
        st.error(f"후보 검색 실패: {exc}")

if issues := st.session_state.get("discovery_result"):
    selected=[]
    for issue in issues:
        st.markdown(f"#### {issue['category']} | {issue['title']}")
        st.caption(f"보도 {issue['coverage_count']}건 · 출처 {issue['publisher_count']}곳 · 이슈 중요도 {issue['importance']:.1f}")
        for index, candidate in enumerate(issue["candidates"]):
            key=f"select_{issue['key']}_{index}"
            checked=st.checkbox(f"{candidate['title']} — 적합도 {candidate['suitability']}", key=key)
            st.caption(f"{candidate['publisher']} | {candidate['published_at']} | 본문 {candidate['preview'].get('clean_text_length', 0):,}자 | 이미지 {candidate['preview'].get('body_image_count', 0)}")
            st.link_button("원문 열기", candidate["url"])
            if checked: selected.append(candidate)
        with st.expander("다른 후보"):
            alternatives = issue.get("alternatives", [])
            if alternatives:
                for candidate in alternatives:
                    st.write(f"{candidate['title']} ({candidate['publisher']})")
            else:
                st.write("다른 preview 통과 후보가 없습니다.")
    st.session_state.selected_articles = selected
    if st.button("선택한 기사 본크롤링", type="primary", use_container_width=True):
        normalized=[]; failures=[]
        with st.status("선택한 기사만 본크롤링 중...", expanded=True) as status:
            for candidate in selected:
                try:
                    page=fetch_html(candidate["url"]); article=extract_article(page.url,page.text); article["source_url"]=page.source_url; normalized.append(article)
                except Exception as exc: failures.append(f"{candidate['url']}: {exc}")
            status.update(label=f"본크롤링 완료: {len(normalized)}건", state="complete")
        st.session_state.normalized_articles=normalized
        st.session_state.discovery_failures=st.session_state.get("discovery_failures", [])+failures
        st.success(f"{len(normalized)}개 기사를 Publication Builder에 전달할 준비가 되었습니다.")
    if failures := st.session_state.get("discovery_failures"):
        with st.expander(f"실패 로그 ({len(failures)})"):
            st.code("\n".join(failures))
if diagnostics := st.session_state.get("discovery_diagnostics"):
    with st.expander("검색 진단"):
        st.json(diagnostics)
