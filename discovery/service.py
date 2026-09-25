"""Metadata/issue signals first; only direct publisher URLs proceed to preview."""
from __future__ import annotations
from datetime import date
from pathlib import Path
from urllib.parse import urlparse
import yaml
from crawler.extractor import extract_article
from crawler.fetcher import FetchError, UnsafeUrlError, _allowed_by_robots, validate_public_url, fetch_html
from discovery.clustering import cluster
from discovery.deduplicator import deduplicate
from discovery.ranking import score_preview, select_issues
from discovery.providers.base import NewsSearchProvider

QUERIES=("정치","경제","사회"); EXCLUDE=("연예","스포츠","운세","날씨","쇼핑","광고","포토","영상"); RELAY=("news.google.","google.com","search.naver.","bing.com")
def config(): return yaml.safe_load((Path(__file__).parents[1]/"config/news_selection.yaml").read_text())
def reason(exc):
    text=str(exc).lower()
    if "robots" in text:return "ROBOTS_BLOCKED"
    if "timeout" in text:return "TIMEOUT"
    if "private" in text or "url must" in text:return "INVALID_URL"
    if "paywall" in text or "login" in text:return "PAYWALL"
    return "FETCH_FAILED"
def original_ok(url):
    try: clean=validate_public_url(url)
    except (FetchError,UnsafeUrlError) as exc:return False,reason(exc)
    if any(x in (urlparse(clean).hostname or "") for x in RELAY):return False,"INVALID_URL"
    return (True,"") if _allowed_by_robots(clean,(5,20)) else (False,"ROBOTS_BLOCKED")
def discover(provider: NewsSearchProvider,start: date,end: date):
    cfg=config(); errors=[]; all_items=[]; d={"metadata_candidates":0,"original_urls":0,"relay_urls_skipped":0,"preview_attempted":0,"preview_success":0,"preview_failed":0,"issues_found":0,"recommendations":0,"failure_breakdown":{}}
    for query in QUERIES: all_items+=provider.search(query,start,end,cfg["search"]["per_query_limit"])
    d["metadata_candidates"]=len(all_items); items=deduplicate([x for x in all_items if not any(t in (x.title+x.snippet) for t in EXCLUDE)])
    for x in items:
        if x.crawlable_candidate and x.is_original_url:d["original_urls"]+=1
        else:d["relay_urls_skipped"]+=1
    issues=select_issues(cluster(items)); d["issues_found"]=len(issues)
    for issue in issues:
        good=[]
        for candidate in issue.candidates:
            if not candidate.crawlable_candidate: continue
            valid,why=original_ok(candidate.url)
            if not valid:
                d["preview_failed"]+=1; d["failure_breakdown"][why]=d["failure_breakdown"].get(why,0)+1; errors.append(f"{why}: {candidate.url}"); continue
            d["preview_attempted"]+=1
            try:
                page=fetch_html(candidate.url); article=extract_article(page.url,page.text); length=len(str(article.get("article_text") or "")); images=len(article.get("images") or [])
                if length<cfg["thresholds"]["min_text_length"]: raise ValueError("NO_ARTICLE_BODY")
                candidate.preview={"clean_text_length":length,"body_image_count":images,"crawl_quality":float(article.get("quality",{}).get("score",0)),"title":article.get("title","")}; score_preview(candidate,issue,cfg); good.append(candidate); d["preview_success"]+=1
            except Exception as exc:
                why="NO_ARTICLE_BODY" if "NO_ARTICLE_BODY" in str(exc) else reason(exc); d["preview_failed"]+=1; d["failure_breakdown"][why]=d["failure_breakdown"].get(why,0)+1; errors.append(f"{why}: {candidate.url}")
        ranked=sorted(good,key=lambda x:x.suitability,reverse=True); issue.candidates=ranked[:cfg["selection"]["per_issue"]]; issue.alternatives=ranked[cfg["selection"]["per_issue"]:]
    issues=[x for x in issues if x.candidates]; d["recommendations"]=sum(len(x.candidates) for x in issues)
    return [x.to_dict() for x in issues],errors,d
