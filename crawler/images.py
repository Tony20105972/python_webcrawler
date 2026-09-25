"""Extract editorial images from the selected article body, not the whole page."""
from __future__ import annotations
import re
from urllib.parse import urljoin, urlparse, urlunparse
from bs4 import BeautifulSoup, Tag

NEGATIVE = ("recommend", "related", "relation", "popular", "ranking", "most-read", "more-news", "other-news", "suggest", "promo", "advert", "banner", "subscription", "newsletter", "share", "social", "reporter", "author", "profile", "byline", "footer", "aside", "sidebar", "광고", "관련기사", "추천기사", "인기기사", "기자프로필")
URL_NEGATIVE = ("logo", "favicon", "icon", "avatar", "profile", "advert", "ads", "banner", "tracking", "pixel", "sprite", "thumbnail", "thumb", "recommend")
SCORES = {"body":4, "figure":2, "near_text":2, "caption":1, "lead":2, "semantic":-10, "negative":-8, "card":-6, "repeat":-6, "small":-3, "url":-5}
THRESHOLD = 4

def absolute_url(base_url: str, value: str | None) -> str | None:
    if not value or value.strip().startswith(("data:", "javascript:", "#")): return None
    result = urljoin(base_url, value.strip())
    return result if urlparse(result).scheme in {"http", "https"} else None

def canonical_url(url: str) -> str:
    p = urlparse(url); q = "&".join(x for x in p.query.split("&") if not x.lower().startswith(("utm_", "fbclid=", "gclid=")))
    return urlunparse(p._replace(query=q, fragment=""))

def _source(tag: Tag) -> str | None:
    if tag.name == "img" and tag.find_parent("picture"):
        source = tag.find_parent("picture").find("source")
        if source and (source.get("srcset") or source.get("data-srcset")):
            return _source(source)
    srcset = tag.get("srcset") or tag.get("data-srcset") or tag.get("data-lazy-srcset")
    if srcset:
        choices = []
        for item in srcset.split(","):
            bits = item.strip().split()
            if bits: choices.append((bits[0], int(re.sub(r"\D", "", bits[1]) or 0) if len(bits)>1 else 0))
        if choices: return max(choices, key=lambda x:x[1])[0]
    return tag.get("src") or tag.get("data-src") or tag.get("data-original") or tag.get("data-lazy-src") or tag.get("data-url")

def _marker(tag: Tag) -> str:
    return " ".join([tag.name or "", str(tag.get("id", "")), " ".join(tag.get("class", [])), str(tag.get("role", "")), str(tag.get("aria-label", ""))]).lower()

def _ancestors(tag: Tag, body: Tag) -> list[Tag]:
    result=[]
    for parent in tag.parents:
        if isinstance(parent, Tag):
            result.append(parent)
            if parent is body: break
    return result

def _near_text(tag: Tag) -> bool:
    block = tag.find_parent(["figure", "picture", "div", "p"]) or tag
    return any(p and len(p.get_text(" ", strip=True)) >= 25 for p in (block.find_previous("p"), block.find_next("p")))

def _is_card(tag: Tag, base: str) -> bool:
    link=tag.find_parent("a", href=True)
    if not link: return False
    destination=absolute_url(base, str(link.get("href")))
    title=link.find(["h1","h2","h3","h4","strong"]) or link.find_next_sibling(["h1","h2","h3","h4"])
    return bool(destination and canonical_url(destination) != canonical_url(base) and title)

def _repeated_card(tag: Tag) -> bool:
    card=tag.find_parent(["li","article","div"])
    if not card or not card.parent or not card.get("class"): return False
    same=[s for s in card.parent.find_all(card.name, recursive=False) if s.get("class")==card.get("class")]
    return len(same)>=2 and sum(bool(s.find("img")) and bool(s.find(["h1","h2","h3","h4","strong"])) for s in same)>=2

def _details(tag: Tag, url: str) -> dict[str, object]:
    figure=tag.find_parent("figure"); caption_tag=figure.find("figcaption") if figure else None
    credit=figure.select_one("[class*='credit' i], [class*='copyright' i], [class*='source' i]") if figure else None
    return {"url":url,"caption":caption_tag.get_text(" ",strip=True) if caption_tag else "","alt":str(tag.get("alt","")).strip(),"credit":credit.get_text(" ",strip=True) if credit else "","type":"body"}

def _score(tag: Tag, url: str, body: Tag, base: str, lead: str | None) -> tuple[int,list[str]]:
    score,reasons=SCORES["body"],["inside_article_body"]; ancestors=_ancestors(tag,body)
    if tag.find_parent("figure"): score+=SCORES["figure"]; reasons.append("inside_figure")
    if _near_text(tag): score+=SCORES["near_text"]; reasons.append("near_article_paragraph")
    if tag.find_parent("figure") and tag.find_parent("figure").find("figcaption"): score+=SCORES["caption"]; reasons.append("has_caption")
    if lead and canonical_url(url)==canonical_url(lead): score+=SCORES["lead"]; reasons.append("matches_metadata_lead")
    if any(a.name in {"aside","nav","footer"} for a in ancestors): score+=SCORES["semantic"]; reasons.append("semantic_exclusion")
    if any(any(word in _marker(a) for word in NEGATIVE) for a in ancestors): score+=SCORES["negative"]; reasons.append("negative_container")
    if _is_card(tag,base): score+=SCORES["card"]; reasons.append("linked_other_article_card")
    if _repeated_card(tag): score+=SCORES["repeat"]; reasons.append("repeated_thumbnail_card")
    if any(word in (url+" "+_marker(tag)).lower() for word in URL_NEGATIVE) or url.split("?")[0].endswith(".svg"): score+=SCORES["url"]; reasons.append("utility_url")
    try:
        if int(tag.get("width") or 999)<=80 or int(tag.get("height") or 999)<=80: score+=SCORES["small"]; reasons.append("small_dimensions")
    except ValueError: pass
    return score,reasons

def extract_images(soup: BeautifulSoup, base_url: str, lead_image: str | None = None, body_container: Tag | None = None, debug: bool = False):
    body=body_container or soup.select_one("article, [itemprop='articleBody'], main, [role='main']"); decisions=[]; items=[]
    if not body: return (items,decisions) if debug else items
    for tag in body.select("img"):
        url=absolute_url(base_url,_source(tag))
        if not url: continue
        score,reasons=_score(tag,url,body,base_url,lead_image); included=score>=THRESHOLD
        decisions.append({"url":url,"decision":"included" if included else "excluded","score":score,"reasons":reasons})
        if included:
            item=_details(tag,url); item["confidence"]=round(min(score/10,1),2); items.append(item)
    unique={}
    for item in items: unique.setdefault(canonical_url(str(item["url"])),item)
    result=list(unique.values())
    return (result,decisions) if debug else result
