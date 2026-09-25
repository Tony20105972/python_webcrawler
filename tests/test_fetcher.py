from unittest.mock import patch

import pytest

from crawler.fetcher import UnsafeUrlError, validate_public_url


@patch("crawler.fetcher.socket.getaddrinfo")
def test_rejects_private_ip_after_dns_resolution(mock_lookup):
    mock_lookup.return_value = [(None, None, None, None, ("127.0.0.1", 80))]
    with pytest.raises(UnsafeUrlError):
        validate_public_url("https://example.test/article")


def test_rejects_non_http_urls():
    with pytest.raises(Exception):
        validate_public_url("file:///tmp/article.html")
