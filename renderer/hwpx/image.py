"""Embed local assets in BinData and emit inline, aspect-ratio-preserving pictures."""
from pathlib import Path
from PIL import Image

_counter = 5000
def _id() -> str:
    global _counter; _counter += 1; return str(_counter)

def image_dimensions(path: Path, max_width_mm: float = 150, max_height_mm: float = 105) -> tuple[int, int]:
    with Image.open(path) as picture:
        width, height = picture.size
    scale = min(max_width_mm * 283.5 / width, max_height_mm * 283.5 / height, 1)
    return int(width * scale), int(height * scale)

def image_paragraph(binary_id: str, path: Path) -> str:
    width, height = image_dimensions(path); half_w, half_h = width // 2, height // 2
    p, pic, inst = _id(), _id(), _id()
    return f'''<hp:p id="{p}" paraPrIDRef="0" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0"><hp:run charPrIDRef="0"><hp:pic id="{pic}" zOrder="0" numberingType="PICTURE" textWrap="TOP_AND_BOTTOM" textFlow="BOTH_SIDES" lock="0" dropcapstyle="None" href="" groupLevel="0" instid="{inst}" reverse="0"><hp:offset x="0" y="0"/><hp:orgSz width="{width}" height="{height}"/><hp:curSz width="{width}" height="{height}"/><hp:flip horizontal="0" vertical="0"/><hp:rotationInfo angle="0" centerX="{half_w}" centerY="{half_h}" rotateimage="0"/><hp:renderingInfo><hc:transMatrix e1="1" e2="0" e3="0" e4="0" e5="1" e6="0"/><hc:scaMatrix e1="1" e2="0" e3="0" e4="0" e5="1" e6="0"/><hc:rotMatrix e1="1" e2="0" e3="0" e4="0" e5="1" e6="0"/></hp:renderingInfo><hc:img binaryItemIDRef="{binary_id}" bright="0" contrast="0" effect="REAL_PIC" alpha="0"/><hp:imgRect><hc:pt0 x="0" y="0"/><hc:pt1 x="{width}" y="0"/><hc:pt2 x="{width}" y="{height}"/><hc:pt3 x="0" y="{height}"/></hp:imgRect><hp:imgClip left="0" right="{width}" top="0" bottom="{height}"/><hp:inMargin left="0" right="0" top="0" bottom="0"/><hp:imgDim dimwidth="{width}" dimheight="{height}"/><hp:effects/><hp:sz width="{width}" widthRelTo="ABSOLUTE" height="{height}" heightRelTo="ABSOLUTE" protect="0"/><hp:pos treatAsChar="1" affectLSpacing="0" flowWithText="1" allowOverlap="0" holdAnchorAndSO="0" vertRelTo="PARA" horzRelTo="COLUMN" vertAlign="TOP" horzAlign="CENTER" vertOffset="0" horzOffset="0"/><hp:outMargin left="0" right="0" top="0" bottom="0"/></hp:pic><hp:t/></hp:run></hp:p>'''
