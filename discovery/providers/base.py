from __future__ import annotations
from abc import ABC, abstractmethod
from datetime import date
from discovery.models import Candidate

class NewsSearchProvider(ABC):
    @abstractmethod
    def search(self, query: str, start_date: date, end_date: date, limit: int) -> list[Candidate]: ...
