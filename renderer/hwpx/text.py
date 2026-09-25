from xml.sax.saxutils import escape

def safe_text(value: object) -> str:
    return escape(str(value or ""), {'"': '&quot;', "'": '&apos;'})
