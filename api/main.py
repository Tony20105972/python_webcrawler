"""HTTP adapter for the Python crawler; it owns no extraction logic."""
from __future__ import annotations

import sys
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from crawler.extractor import extract_article  # noqa: E402
from crawler.fetcher import FetchError, UnsafeUrlError, fetch_html  # noqa: E402

app = FastAPI(title="News Crawler API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=False,
    allow_methods=["POST"],
    allow_headers=["Content-Type"],
)


class ExtractRequest(BaseModel):
    url: HttpUrl


@app.post("/api/extract")
def extract(request: ExtractRequest) -> dict:
    try:
        page = fetch_html(str(request.url))
        article = extract_article(page.url, page.text)
        article["source_url"] = page.source_url
    except UnsafeUrlError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except FetchError as exc:
        raise HTTPException(status_code=502, detail=f"Page access failed: {exc}") from exc
    except Exception:
        # Do not expose parser/library traces to browser clients.
        raise HTTPException(status_code=500, detail="Article extraction failed.")
    if not article.get("article_text"):
        raise HTTPException(status_code=422, detail="Article body could not be found.")
    return article
