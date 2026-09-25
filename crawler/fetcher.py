"""Safe, conventional HTTP retrieval for public article pages."""
from __future__ import annotations

from dataclasses import dataclass

import requests

DEFAULT_TIMEOUT = (5, 20)  # connect, read seconds
USER_AGENT = "NewsCrawlerMVP/0.1 (+https://github.com/example/news-crawler)"


class FetchError(RuntimeError):
    """An article page could not be fetched."""


@dataclass(frozen=True)
class FetchedPage:
    url: str
    text: str
    content_type: str


def fetch_html(url: str, timeout: tuple[int, int] = DEFAULT_TIMEOUT) -> FetchedPage:
    """Fetch a public HTML page, following normal HTTP redirects."""
    if not url.startswith(("http://", "https://")):
        raise FetchError("URL must start with http:// or https://")

    try:
        response = requests.get(
            url,
            headers={"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml"},
            timeout=timeout,
            allow_redirects=True,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise FetchError(str(exc)) from exc

    content_type = response.headers.get("Content-Type", "").lower()
    if content_type and "html" not in content_type and "xhtml" not in content_type:
        raise FetchError(f"Expected an HTML page, received {content_type}")
    return FetchedPage(url=response.url, text=response.text, content_type=content_type)
