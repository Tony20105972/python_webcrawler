"""Safe, conventional HTTP retrieval for public article pages."""
from __future__ import annotations

from dataclasses import dataclass
import ipaddress
import socket
from functools import lru_cache
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import requests

DEFAULT_TIMEOUT = (5, 20)  # connect, read seconds
USER_AGENT = "NewsCrawlerMVP/0.1 (+https://github.com/example/news-crawler)"
MAX_REDIRECTS = 5


class FetchError(RuntimeError):
    """An article page could not be fetched."""


class UnsafeUrlError(FetchError):
    """The requested address is local or otherwise unsuitable for fetching."""


@dataclass(frozen=True)
class FetchedPage:
    url: str
    source_url: str
    text: str
    content_type: str


def validate_public_url(url: str) -> str:
    """Validate an HTTP URL and reject loopback/private network destinations."""
    parsed = urlparse(url.strip())
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise FetchError("URL must use http:// or https:// and include a host")
    if parsed.username or parsed.password:
        raise UnsafeUrlError("URLs containing account credentials are not allowed")
    try:
        addresses = {item[4][0] for item in socket.getaddrinfo(parsed.hostname, parsed.port or 443, type=socket.SOCK_STREAM)}
    except socket.gaierror as exc:
        raise FetchError("The host name could not be resolved") from exc
    for address in addresses:
        candidate = ipaddress.ip_address(address)
        if not candidate.is_global:
            raise UnsafeUrlError("Local, private, or reserved network addresses are not allowed")
    return parsed.geturl()


@lru_cache(maxsize=128)
def _robots_rules(scheme: str, netloc: str, timeout: tuple[int, int]) -> RobotFileParser | None:
    """Retrieve robots rules once per site during this process."""
    robots_url = f"{scheme}://{netloc}/robots.txt"
    parser = RobotFileParser()
    parser.set_url(robots_url)
    try:
        response = requests.get(robots_url, headers={"User-Agent": USER_AGENT}, timeout=timeout)
        if response.status_code == 200:
            parser.parse(response.text.splitlines())
            return parser
    except requests.RequestException:
        pass
    return None


def _allowed_by_robots(url: str, timeout: tuple[int, int]) -> bool:
    """Honor a published robots.txt rule; unreachable robots files do not block access."""
    parsed = urlparse(url)
    parser = _robots_rules(parsed.scheme, parsed.netloc, timeout)
    return parser.can_fetch(USER_AGENT, url) if parser else True


def fetch_html(url: str, timeout: tuple[int, int] = DEFAULT_TIMEOUT) -> FetchedPage:
    """Fetch one public HTML page, respecting robots.txt and checking redirects."""
    current_url = validate_public_url(url)
    source_url = current_url

    try:
        for _ in range(MAX_REDIRECTS + 1):
            if not _allowed_by_robots(current_url, timeout):
                raise FetchError("This page is disallowed by the site's robots.txt policy")
            response = requests.get(
                current_url,
                headers={"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml"},
                timeout=timeout,
                allow_redirects=False,
            )
            if not response.is_redirect:
                break
            location = response.headers.get("Location")
            if not location:
                raise FetchError("The server returned a redirect without a destination")
            current_url = validate_public_url(urljoin(current_url, location))
        else:
            raise FetchError("Too many redirects while opening the article")
        response.raise_for_status()
    except requests.RequestException as exc:
        raise FetchError(str(exc)) from exc

    content_type = response.headers.get("Content-Type", "").lower()
    if content_type and "html" not in content_type and "xhtml" not in content_type:
        raise FetchError(f"Expected an HTML page, received {content_type}")
    return FetchedPage(url=response.url, source_url=source_url, text=response.text, content_type=content_type)
