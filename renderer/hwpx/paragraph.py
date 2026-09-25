"""Flowing paragraph XML: no per-article page breaks are emitted."""
from .text import safe_text

_counter = 1000
def _id() -> str:
    global _counter; _counter += 1; return str(_counter)

def paragraph(text: str, char_pr: str, para_pr: str, page_break: bool = False) -> str:
    return f'<hp:p id="{_id()}" paraPrIDRef="{para_pr}" styleIDRef="0" pageBreak="{int(page_break)}" columnBreak="0" merged="0"><hp:run charPrIDRef="{char_pr}"><hp:t>{safe_text(text)}</hp:t></hp:run></hp:p>'

def section_start(secpr: str, colpr: str) -> str:
    return f'<hp:p id="{_id()}" paraPrIDRef="0" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0"><hp:run charPrIDRef="0">{secpr}{colpr}</hp:run></hp:p>'
