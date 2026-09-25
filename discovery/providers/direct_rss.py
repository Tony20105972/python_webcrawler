"""Official publisher RSS provider; accepts only feeds whose item links are publisher URLs."""
from __future__ import annotations
from datetime import date
from pathlib import Path
from urllib.parse import urlparse
import feedparser, requests, yaml
from .base import NewsSearchProvider
from discovery.models import Candidate

RELAY_HOSTS=("news.google.", "google.com", "search.naver.", "bing.com")
def is_original_url(url: str, publisher_host: str | None = None) -> bool:
    host=urlparse(url).hostname or ""
    return urlparse(url).scheme in {"http","https"} and not any(item in host for item in RELAY_HOSTS) and (not publisher_host or host.endswith(publisher_host))

class DirectPublisherRssProvider(NewsSearchProvider):
    def __init__(self, sources_path: str | Path | None = None):
        path=Path(sources_path or Path(__file__).parents[2]/"config/news_sources.yaml")
        self.sources=yaml.safe_load(path.read_text(encoding="utf-8")).get("sources", [])
        self.diagnostics={"feeds_checked":0,"feeds_valid":0,"feeds_skipped":0,"original_urls":0}
    def search(self, query: str, start_date: date, end_date: date, limit: int) -> list[Candidate]:
        candidates=[]
        for source in self.sources:
            if not source.get("enabled") or source.get("category") != query: continue
            self.diagnostics["feeds_checked"]+=1
            try:
                response=requests.get(source["rss_url"],timeout=(5,15),headers={"User-Agent":"NewsCrawlerMVP/0.1"}); response.raise_for_status()
                feed=feedparser.parse(response.content)
                if not feed.entries: raise ValueError("empty or invalid RSS")
                publisher_host=urlparse(source["rss_url"]).hostname or ""
                valid=[]
                for entry in feed.entries:
                    link=entry.get("link",""); title=entry.get("title",""); published=entry.get("published",entry.get("updated",""))
                    if not (link and title and published and is_original_url(link,publisher_host)): continue
                    valid.append(Candidate(url=link,canonical_url=link,title=title,snippet=entry.get("summary", ""),publisher=source["name"],published_at=published,category=source["category"],discovery_source="official_rss",is_original_url=True,crawlable_candidate=True))
                if not valid: raise ValueError("no direct recent item links")
                self.diagnostics["feeds_valid"]+=1; self.diagnostics["original_urls"]+=len(valid); candidates.extend(valid[:limit])
            except Exception:
                self.diagnostics["feeds_skipped"]+=1
        return candidates
