from weekly.input_parser import parse_sections
from weekly.models import Article, Publication, Section
from weekly.validate import validate_publication


def test_parses_grouped_weekly_urls():
    result = parse_sections("주간시사 1\n주제: 정치\nhttps://example.com/a\n\n주간시사 2\n주제: 경제\nhttps://example.com/b")
    assert result[0]["section_number"] == 1
    assert result[1]["section_title"] == "경제"


def test_validator_finds_required_article_fields():
    publication = Publication({}, {}, [Section(1, "정치", [Article()])])
    report = validate_publication(publication)
    assert report["valid"] is False
    assert any("제목 누락" in item["message"] for item in report["issues"])
