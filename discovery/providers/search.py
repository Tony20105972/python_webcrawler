"""Public RSS provider: returns search metadata only, never article bodies."""
from __future__ import annotations
from datetime import date
from email.utils import parsedate_to_datetime
from urllib.parse import quote_plus
import feedparser
import requests
from .base import NewsSearchProvider
from discovery.models import Candidate

class GoogleNewsRssProvider(NewsSearchProvider):
    def search(self, query: str, start_date: date, end_date: date, limit: int) -> list[Candidate]:
        days = max((end_date - start_date).days + 1, 1)
        url = "https://news.google.com/rss/search?q=" + quote_plus(f"{query} when:{days}d") + "&hl=ko&gl=KR&ceid=KR:ko"
        try:
            response = requests.get(url, timeout=(5, 15), headers={"User-Agent": "NewsCrawlerMVP/0.1"}); response.raise_for_status()
            feed = feedparser.parse(response.content)
        except requests.RequestException:
            return []
        result=[]
        for entry in feed.entries[:limit]:
            try: published = parsedate_to_datetime(entry.get("published", "")).date().isoformat()
            except (TypeError, ValueError): published = ""
            source = entry.get("source", {})
            result.append(Candidate(url=entry.get("link", ""), canonical_url=entry.get("link", ""), title=entry.get("title", ""), snippet=entry.get("summary", ""), publisher=source.get("title", "") if isinstance(source, dict) else "", published_at=published, discovery_source="google_news", is_original_url=False, crawlable_candidate=False))
        return [c for c in result if c.url and c.title]
