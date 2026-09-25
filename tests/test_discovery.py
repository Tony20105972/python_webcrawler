from discovery.clustering import cluster
from discovery.deduplicator import deduplicate
from discovery.models import Candidate, Issue
from discovery.ranking import score_preview, select_issues


def test_url_and_near_duplicate_titles_are_removed():
    items = [Candidate("https://a.test/x", "정부 경제 대책 발표"), Candidate("https://b.test/y", "정부 경제대책 발표"), Candidate("https://a.test/x", "다른 제목")]
    assert len(deduplicate(items)) == 1


def test_category_cluster_and_suitability_are_separate():
    candidates = [Candidate("https://a.test/1", "국회 정부 정책 논의", snippet="대통령 국회"), Candidate("https://b.test/2", "금리 물가 경제 전망", snippet="금융시장")]
    issues = cluster(candidates)
    assert {item.category for item in issues} >= {"정치", "경제"}
    issue = Issue("국회 정책", "국회 정책", "정치", [candidates[0]])
    candidates[0].preview = {"clean_text_length": 3000, "body_image_count": 3, "crawl_quality": 1}
    cfg = {"thresholds":{"target_text_length":3000,"target_image_count":3}, "selection":{"weights":{"text_length":.4,"body_images":.3,"issue_relevance":.2,"crawl_quality":.1}}}
    assert score_preview(candidates[0], issue, cfg) > 0
    assert select_issues(issues, 4)
