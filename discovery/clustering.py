from __future__ import annotations
import re
from collections import Counter
from discovery.models import Candidate, Issue

CATEGORIES={"정치":("대통령","국회","정부","여당","야당","민주당","국민의힘","선거","외교","장관"),"경제":("경제","금리","물가","환율","주식","부동산","기업","예산","반도체","금융"),"사회":("사회","의료","교육","법원","사건","사고","노동","복지","환경","재판")}
STOP={"오늘","관련","뉴스","정부","대한","위해","이후","이번","있는","한다","전망","속보"}
def classify(candidate: Candidate) -> str:
    if candidate.discovery_source == "official_rss" and candidate.category in CATEGORIES:
        return candidate.category
    text=(candidate.title+" "+candidate.snippet).lower()
    return max(CATEGORIES, key=lambda key: sum(word in text for word in CATEGORIES[key]))
def _key(candidate: Candidate) -> str:
    tokens=[x for x in re.findall(r"[가-힣]{2,}|[A-Za-z]{3,}",candidate.title) if x not in STOP]
    return " ".join(tokens[:3]) or candidate.title[:30]
def cluster(candidates: list[Candidate]) -> list[Issue]:
    groups={}
    for item in candidates:
        item.category=classify(item); key=_key(item)
        # Merge title candidates sharing their strongest Korean keyword.
        match=next((old for old in groups if set(old.split()) & set(key.split())), key)
        groups.setdefault(match,[]).append(item)
    issues=[]
    for key, items in groups.items():
        issues.append(Issue(key=key,title=key,category=Counter(x.category for x in items).most_common(1)[0][0],candidates=items,coverage_count=len(items),publisher_count=len({x.publisher for x in items if x.publisher}),importance=len(items)+len({x.publisher for x in items if x.publisher})*.5))
    return sorted(issues,key=lambda x:x.importance,reverse=True)
