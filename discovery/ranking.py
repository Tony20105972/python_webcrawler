from __future__ import annotations
from discovery.models import Candidate, Issue

def score_preview(candidate: Candidate, issue: Issue, config: dict) -> float:
    p=candidate.preview; t=config["thresholds"]; w=config["selection"]["weights"]
    text=min(float(p.get("clean_text_length",0))/t["target_text_length"],1)
    images=min(float(p.get("body_image_count",0))/t["target_image_count"],1)
    relevance=sum(token in (candidate.title+candidate.snippet) for token in issue.key.split())/max(len(issue.key.split()),1)
    quality=float(p.get("crawl_quality",0))
    candidate.suitability=round(100*(text*w["text_length"]+images*w["body_images"]+relevance*w["issue_relevance"]+quality*w["crawl_quality"]),1)
    return candidate.suitability

def select_issues(issues: list[Issue], limit: int=4) -> list[Issue]:
    selected=[]
    for category in ("정치","경제","사회"):
        if match:=next((x for x in issues if x.category==category),None): selected.append(match)
    for issue in issues:
        if issue not in selected and len(selected)<limit: selected.append(issue)
    return selected[:limit]
