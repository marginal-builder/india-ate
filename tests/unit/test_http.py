"""Unit tests for HttpFetcher protocol and HttpxFetcher transport."""

import httpx
import pytest

from india_ate.adapters.http import HttpFetcher, HttpxFetcher


def test_httpx_fetcher_implements_protocol_and_get_post() -> None:
    seen_requests: list[tuple[str, str]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen_requests.append((request.method, str(request.url)))
        if request.method == "GET":
            return httpx.Response(200, content=b"<html>ok</html>")
        return httpx.Response(200, content=b'{"status":"ok"}')

    fetcher = HttpxFetcher(transport=httpx.MockTransport(handler))
    assert isinstance(fetcher, HttpFetcher)

    get_bytes = fetcher.get("https://hygiene.fssai.gov.in/test", params={"state": "15"})
    post_bytes = fetcher.post("https://hygiene.fssai.gov.in/api", data={"page": "1"})

    assert get_bytes == b"<html>ok</html>"
    assert post_bytes == b'{"status":"ok"}'
    assert seen_requests == [
        ("GET", "https://hygiene.fssai.gov.in/test?state=15"),
        ("POST", "https://hygiene.fssai.gov.in/api"),
    ]


def test_httpx_fetcher_raises_on_http_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, content=b"Service Unavailable")

    fetcher = HttpxFetcher(transport=httpx.MockTransport(handler))
    with pytest.raises(httpx.HTTPStatusError):
        fetcher.get("https://hygiene.fssai.gov.in/down")
