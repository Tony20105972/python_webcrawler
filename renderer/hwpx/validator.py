"""Strict post-build package validation. No validation PASS means no build success."""
from __future__ import annotations
import json
from pathlib import Path
from xml.etree import ElementTree
from zipfile import ZIP_STORED, BadZipFile, ZipFile

REQUIRED = {"mimetype", "Contents/content.hpf", "Contents/header.xml", "Contents/section0.xml", "version.xml"}
def validate(path: str, publication_json: str | None = None) -> list[str]:
    errors: list[str] = []
    try: archive = ZipFile(path)
    except BadZipFile: return ["ZIP package cannot be opened"]
    with archive:
        names = archive.namelist(); missing = REQUIRED - set(names)
        errors += [f"missing required package part: {name}" for name in sorted(missing)]
        if names and names[0] != "mimetype": errors.append("mimetype is not first ZIP entry")
        if "mimetype" in names:
            if archive.read("mimetype").decode().strip() != "application/hwp+zip": errors.append("invalid HWPX mimetype")
            if archive.getinfo("mimetype").compress_type != ZIP_STORED: errors.append("mimetype must be uncompressed")
        for name in names:
            if name.endswith((".xml", ".hpf")):
                try: ElementTree.fromstring(archive.read(name))
                except ElementTree.ParseError as exc: errors.append(f"invalid XML {name}: {exc}")
        if "Contents/content.hpf" in names:
            hpf = archive.read("Contents/content.hpf").decode("utf-8")
            for binary in [name for name in names if name.startswith("BinData/")]:
                if binary.removeprefix("BinData/") not in hpf: errors.append(f"embedded image missing manifest reference: {binary}")
        if publication_json and "Contents/section0.xml" in names:
            rendered = archive.read("Contents/section0.xml").decode("utf-8")
            source = json.loads(Path(publication_json).read_text(encoding="utf-8"))
            for section in source.get("sections", []):
                for article in section.get("articles", []):
                    if not article.get("title"): errors.append("source article has missing title")
                    elif article["title"] not in rendered: errors.append(f"missing rendered article title: {article['title']}")
                    if not article.get("body"): errors.append(f"source article has missing body: {article.get('title', '')}")
    return errors
