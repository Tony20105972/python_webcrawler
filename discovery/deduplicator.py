from __future__ import annotations
import re
from difflib import SequenceMatcher
from discovery.models import Candidate

def _norm(value: str) -> str: return re.sub(r"[^가-힣a-z0-9]", "", value.lower())
def deduplicate(candidates: list[Candidate]) -> list[Candidate]:
    kept=[]; seen=set()
    for item in candidates:
        key=item.canonical_url.split("?")[0]
        if key in seen or any(SequenceMatcher(None, _norm(item.title), _norm(old.title)).ratio() > .88 for old in kept): continue
        seen.add(key); kept.append(item)
    return kept
