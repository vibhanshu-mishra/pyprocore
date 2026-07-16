"""Async transport abstractions for PyProcore.

The transport layer is intentionally small so Phase 10A can test async client
behavior without making live HTTP calls. A real HTTP transport is available when
the optional ``httpx`` dependency is installed.
"""

from __future__ import annotations

import importlib
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any, Protocol, Self, cast
from urllib.parse import urlencode, urlsplit, urlunsplit

from pyprocore.core.exceptions import ConfigurationError


@dataclass(frozen=True)
class AsyncRequest:
    """A sanitized record of one async transport request."""

    method: str
    url: str
    params: Mapping[str, Any] | None = None
    headers: Mapping[str, str] | None = None
    json: Mapping[str, Any] | None = None
    timeout: int | None = None

    @property
    def path_url(self) -> str:
        """Return the request path with query string."""
        parsed = urlsplit(self.url)
        query = parsed.query
        if self.params:
            query = urlencode(self.params, doseq=True)
        return urlunsplit(("", "", parsed.path, query, ""))


@dataclass
class AsyncResponse:
    """Small response object consumed by the async client."""

    status_code: int
    url: str
    headers: Mapping[str, str] = field(default_factory=dict)
    json_data: Any | None = None
    text: str = ""
    content: bytes = b""
    request: AsyncRequest | None = None

    @property
    def ok(self) -> bool:
        """Return whether the HTTP status is successful."""
        return 200 <= self.status_code < 400

    def json(self) -> Any:
        """Return the configured JSON payload."""
        if self.json_data is None:
            raise ValueError("Response does not include JSON data.")
        return self.json_data


class AsyncTransport(Protocol):
    """Protocol implemented by async HTTP transports."""

    async def request(
        self,
        *,
        method: str,
        url: str,
        params: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
        json: Mapping[str, Any] | None = None,
        timeout: int | None = None,
    ) -> AsyncResponse:
        """Send an async request and return an async response."""

    async def close(self) -> None:
        """Close transport resources."""


class MockAsyncTransport:
    """In-memory async transport for tests and documentation examples."""

    def __init__(self, responses: Sequence[AsyncResponse] | None = None) -> None:
        """Initialize the mock transport.

        Args:
            responses: Ordered responses returned by subsequent requests.
        """
        self._responses = list(responses or [])
        self.requests: list[AsyncRequest] = []
        self.closed = False

    def add_response(self, response: AsyncResponse) -> None:
        """Append one response to the mock response queue."""
        self._responses.append(response)

    async def request(
        self,
        *,
        method: str,
        url: str,
        params: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
        json: Mapping[str, Any] | None = None,
        timeout: int | None = None,
    ) -> AsyncResponse:
        """Return the next queued response without making a network call."""
        request = AsyncRequest(
            method=method.upper(),
            url=url,
            params=params,
            headers=headers,
            json=json,
            timeout=timeout,
        )
        self.requests.append(request)
        if not self._responses:
            raise AssertionError(f"No mock async response queued for {method.upper()} {url}.")
        response = self._responses.pop(0)
        response.request = request
        if not response.url:
            response.url = url
        return response

    async def close(self) -> None:
        """Mark the mock transport as closed."""
        self.closed = True


class HttpxAsyncTransport:
    """Optional real async HTTP transport backed by ``httpx``."""

    def __init__(self) -> None:
        """Initialize the optional transport.

        Raises:
            ConfigurationError: If the optional ``httpx`` dependency is missing.
        """
        try:
            httpx_module = importlib.import_module("httpx")
        except ImportError as exc:
            raise ConfigurationError(
                "Async HTTP transport requires the optional dependency httpx. "
                "Install it with `pip install pyprocore[async]`."
            ) from exc
        self._client = httpx_module.AsyncClient()

    async def request(
        self,
        *,
        method: str,
        url: str,
        params: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
        json: Mapping[str, Any] | None = None,
        timeout: int | None = None,
    ) -> AsyncResponse:
        """Send one request with ``httpx`` and adapt the response."""
        response = await self._client.request(
            method=method,
            url=url,
            params=params,
            headers=headers,
            json=json,
            timeout=timeout,
        )
        request = AsyncRequest(
            method=method.upper(),
            url=str(response.request.url),
            params=params,
            headers=headers,
            json=json,
            timeout=timeout,
        )
        json_data: Any | None = None
        content_type = response.headers.get("Content-Type", "")
        if "application/json" in content_type:
            json_data = response.json()
        return AsyncResponse(
            status_code=response.status_code,
            url=str(response.url),
            headers=dict(response.headers),
            json_data=json_data,
            text=response.text,
            content=response.content,
            request=request,
        )

    async def close(self) -> None:
        """Close the underlying ``httpx`` async client."""
        close = cast(Any, self._client.aclose)
        await close()

    async def __aenter__(self) -> Self:
        """Return this transport for async context manager use."""
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: object | None,
    ) -> None:
        """Close the transport when leaving an async context."""
        await self.close()


__all__ = [
    "AsyncRequest",
    "AsyncResponse",
    "AsyncTransport",
    "HttpxAsyncTransport",
    "MockAsyncTransport",
]
