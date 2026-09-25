from __future__ import annotations
from datetime import date
from .base import NewsSearchProvider
from discovery.deduplicator import deduplicate
from discovery.models import Candidate

class CompositeNewsSearchProvider(NewsSearchProvider):
    def __init__(self, providers: list[NewsSearchProvider]): self.providers=providers; self.failures=[]
    def search(self, query: str, start_date: date, end_date: date, limit: int) -> list[Candidate]:
        items=[]
        for provider in self.providers:
            try: items.extend(provider.search(query,start_date,end_date,limit))
            except Exception as exc: self.failures.append(f"{type(provider).__name__}: {exc}")
        return deduplicate(items)
