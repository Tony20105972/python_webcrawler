#!/usr/bin/env python3
"""Build a validated HWPX weekly issue from publication.json."""
from __future__ import annotations
import argparse
from pathlib import Path
from renderer.hwpx.document import render
from renderer.hwpx.validator import validate

parser = argparse.ArgumentParser()
parser.add_argument("publication", nargs="?")
parser.add_argument("--input", dest="input_path")
parser.add_argument("--output", default="output/2026_주간시사_9월4주.hwpx")
args = parser.parse_args()
source = args.input_path or args.publication
if not source:
    parser.error("publication.json 또는 --input이 필요합니다.")
try:
    result = render(source, args.output)
    failures = validate(str(result), str(source))
    if failures:
        print("BUILD FAILED")
        for failure in failures: print(f"- {failure}")
        raise SystemExit(1)
    print("BUILD SUCCESS")
    print(result)
except Exception as exc:
    print("BUILD FAILED")
    print(f"- {exc}")
    raise SystemExit(1)
