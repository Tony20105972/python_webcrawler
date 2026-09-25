"""Parse the deliberately simple multi-section URL input format."""
from __future__ import annotations

import re

SECTION_RE = re.compile(r"^주간시사\s*(\d+)\s*$", re.I)
TOPIC_RE = re.compile(r"^주제\s*:\s*(.+)$")


def parse_sections(value: str) -> list[dict[str, object]]:
    sections: list[dict[str, object]] = []
    current: dict[str, object] | None = None
    for raw in value.splitlines():
        line = raw.strip()
        if not line:
            continue
        if match := SECTION_RE.match(line):
            current = {"section_number": int(match.group(1)), "section_title": "", "urls": []}
            sections.append(current)
        elif match := TOPIC_RE.match(line):
            if current is None:
                raise ValueError("'주제:' 앞에 '주간시사 N'을 먼저 입력해 주세요.")
            current["section_title"] = match.group(1).strip()
        elif line.startswith(("http://", "https://")):
            if current is None:
                raise ValueError("URL 앞에 '주간시사 N'을 먼저 입력해 주세요.")
            current["urls"].append(line)
        else:
            raise ValueError(f"인식할 수 없는 줄입니다: {line}")
    if not sections:
        raise ValueError("최소 한 개의 '주간시사 N' 섹션을 입력해 주세요.")
    for section in sections:
        if not section["section_title"]:
            raise ValueError(f"주간시사 {section['section_number']}의 주제를 입력해 주세요.")
        if not section["urls"]:
            raise ValueError(f"주간시사 {section['section_number']}에 URL을 하나 이상 입력해 주세요.")
    return sections
