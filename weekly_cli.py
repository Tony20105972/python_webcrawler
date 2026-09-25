"""Build and render a weekly issue from a simple section/URL text file."""
from __future__ import annotations
import argparse, json
from pathlib import Path
from weekly.input_parser import parse_sections
from weekly.pipeline import build_publication, load_publication
from weekly.renderer import render_pdf
from weekly.validate import validate_publication

parser = argparse.ArgumentParser(description="Create a weekly current-affairs PDF from grouped article URLs.")
parser.add_argument("input", help="UTF-8 section/URL text file")
parser.add_argument("--workspace", required=True)
parser.add_argument("--issue", default="2026년 9월 3주")
parser.add_argument("--render-only", action="store_true")
args = parser.parse_args()
root = Path(args.workspace)
publication = load_publication(root / "publication.json") if args.render_only else build_publication(parse_sections(Path(args.input).read_text(encoding="utf-8")), root, {"issue_label": args.issue, "year": "2026"})
report = validate_publication(publication, root)
(root / "validation.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
render_pdf(publication, root / "weekly-current-affairs.pdf", root)
print(root / "weekly-current-affairs.pdf")
