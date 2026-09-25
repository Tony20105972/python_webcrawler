from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Any

@dataclass
class Candidate:
    url: str; title: str; snippet: str = ""; publisher: str = ""; published_at: str = ""; category: str = "사회"; canonical_url: str = ""; discovery_source: str = "unknown"; is_original_url: bool = True; crawlable_candidate: bool = True; preview: dict[str, Any] = field(default_factory=dict); suitability: float = 0.0
    def to_dict(self): return asdict(self)

@dataclass
class Issue:
    key: str; title: str; category: str; candidates: list[Candidate] = field(default_factory=list); alternatives: list[Candidate] = field(default_factory=list); coverage_count: int = 0; publisher_count: int = 0; importance: float = 0.0
    def to_dict(self): return {**asdict(self), "candidates": [c.to_dict() for c in self.candidates], "alternatives": [c.to_dict() for c in self.alternatives]}
