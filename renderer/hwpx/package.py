"""Create an actual OWPML/HWPX ZIP package from a known-valid template tree."""
from pathlib import Path
from shutil import copytree
from tempfile import TemporaryDirectory
from zipfile import ZIP_DEFLATED, ZIP_STORED, ZipFile

TEMPLATE = Path(__file__).with_name("template")

def package(output: str | Path, section_xml: str, images: list[tuple[str, Path]], title: str) -> Path:
    output = Path(output); output.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory() as tmp:
        work = Path(tmp) / "hwpx"; copytree(TEMPLATE, work)
        (work / "Contents" / "section0.xml").write_text(section_xml, encoding="utf-8")
        hpf = (work / "Contents" / "content.hpf").read_text(encoding="utf-8")
        hpf = hpf.replace("<opf:title/>", f"<opf:title>{title}</opf:title>")
        items = []
        for image_id, image_path in images:
            ext = image_path.suffix.lower().lstrip("."); ext = "jpg" if ext == "jpeg" else ext
            media = {"jpg":"image/jpeg", "png":"image/png", "gif":"image/gif", "bmp":"image/bmp"}.get(ext, "image/jpeg")
            target = work / "BinData" / f"{image_id}.{ext}"; target.parent.mkdir(exist_ok=True); target.write_bytes(image_path.read_bytes())
            items.append(f'<opf:item id="{image_id}" href="BinData/{target.name}" media-type="{media}" isEmbeded="1"/>')
        (work / "Contents" / "content.hpf").write_text(hpf.replace("</opf:manifest>", "".join(items) + "</opf:manifest>"), encoding="utf-8")
        files = sorted(p for p in work.rglob("*") if p.is_file())
        with ZipFile(output, "w", ZIP_DEFLATED) as archive:
            archive.write(work / "mimetype", "mimetype", compress_type=ZIP_STORED)
            for item in files:
                name = item.relative_to(work).as_posix()
                if name == "mimetype": continue
                archive.write(item, name, compress_type=ZIP_STORED if name == "version.xml" else ZIP_DEFLATED)
    return output
