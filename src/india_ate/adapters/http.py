"""Pluggable HTTP transport abstraction and httpx implementation."""

from typing import Protocol, runtime_checkable

import httpx

DEFAULT_TIMEOUT_SECONDS = 30.0
DEFAULT_USER_AGENT = "india-ate/0.1.0 (+https://github.com/india-ate/india-ate)"


@runtime_checkable
class HttpFetcher(Protocol):
    """Port for fetching raw HTTP bytes without coupling adapters to network IO."""

    def get(
        self,
        url: str,
        params: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
    ) -> bytes:
        """Fetch raw response bytes via HTTP GET."""
        ...

    def post(
        self,
        url: str,
        data: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
    ) -> bytes:
        """Fetch raw response bytes via HTTP POST."""
        ...


class HttpxFetcher:
    """Concrete HttpFetcher backed by httpx.Client."""

    def __init__(
        self,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
        user_agent: str = DEFAULT_USER_AGENT,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self._timeout = timeout
        self._user_agent = user_agent
        self._transport = transport

    def _build_client(self) -> httpx.Client:
        return httpx.Client(
            timeout=self._timeout,
            headers={"User-Agent": self._user_agent},
            transport=self._transport,
        )

    def get(
        self,
        url: str,
        params: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
    ) -> bytes:
        """Perform an HTTP GET request and return raw response bytes."""
        with self._build_client() as client:
            response = client.get(url, params=params, headers=headers)
            response.raise_for_status()
            return response.content

    def post(
        self,
        url: str,
        data: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
    ) -> bytes:
        """Perform an HTTP POST request and return raw response bytes."""
        with self._build_client() as client:
            response = client.post(url, data=data, headers=headers)
            response.raise_for_status()
            return response.content
