"""Async HTTP client foundation for the Procore REST API."""

from __future__ import annotations

import asyncio
from collections.abc import Mapping
from time import perf_counter
from typing import Any, Self
from urllib.parse import parse_qs, urljoin, urlparse

from pyprocore.auth.token_manager import TokenManager
from pyprocore.core.async_transport import AsyncResponse, AsyncTransport, HttpxAsyncTransport
from pyprocore.core.client import (
    DEFAULT_TIMEOUT_SECONDS,
    HTTP_FORBIDDEN,
    HTTP_NO_CONTENT,
    HTTP_NOT_FOUND,
    HTTP_RATE_LIMITED,
    HTTP_UNAUTHORIZED,
    RETRYABLE_STATUS_CODES,
)
from pyprocore.core.config import ProcoreSettings, get_settings
from pyprocore.core.exceptions import (
    AuthenticationError,
    AuthorizationError,
    ProcoreAPIError,
    RateLimitError,
    ResourceNotFoundError,
    TransientAPIError,
)
from pyprocore.core.logger import get_logger, log_api_request, log_exception, sanitize_log_value


class AsyncProcoreClient:
    """Async HTTP client for read-oriented Procore workflows."""

    def __init__(
        self,
        settings: ProcoreSettings | None = None,
        token_manager: TokenManager | None = None,
        transport: AsyncTransport | None = None,
        timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
        retry_attempts: int = 3,
        retry_sleep_seconds: float = 1.0,
    ) -> None:
        """Initialize the async Procore HTTP client.

        Args:
            settings: Optional SDK settings. Defaults to environment-backed settings.
            token_manager: Optional token manager for bearer tokens.
            transport: Optional async transport. Defaults to optional ``httpx``.
            timeout_seconds: Default request timeout.
            retry_attempts: Number of attempts for transient failures.
            retry_sleep_seconds: Base delay between retry attempts.
        """
        self._settings = settings or get_settings()
        self._token_manager = token_manager or TokenManager(settings=self._settings)
        self._transport = transport or HttpxAsyncTransport()
        self._timeout_seconds = timeout_seconds
        self._retry_attempts = max(1, retry_attempts)
        self._retry_sleep_seconds = max(0.0, retry_sleep_seconds)
        self._logger = get_logger("async_client")
        self._last_retry_count = 0

    async def __aenter__(self) -> Self:
        """Return this client for async context manager use."""
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: object | None,
    ) -> None:
        """Close transport resources when leaving an async context."""
        await self.close()

    async def close(self) -> None:
        """Close the underlying async transport."""
        await self._transport.close()

    async def get(
        self,
        path: str,
        params: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> Any:
        """Send an async GET request to Procore."""
        return await self.request("GET", path, params=params, headers=headers)

    async def get_all(
        self,
        path: str,
        params: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> list[Any]:
        """Return all pages for a paginated Procore collection endpoint."""
        collected: list[Any] = []
        next_path: str | None = path
        next_params: dict[str, Any] | None = dict(params or {})

        while next_path is not None:
            response = await self._perform_request(
                "GET",
                next_path,
                params=next_params,
                headers=headers,
            )
            page_data = self._parse_response(response)
            if isinstance(page_data, list):
                collected.extend(page_data)
            elif page_data is not None:
                collected.append(page_data)

            next_path, next_params = self._next_page(response, next_params)

        return collected

    async def request(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        json: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
        timeout_seconds: int | None = None,
    ) -> Any:
        """Send an authenticated async request and parse the response."""
        response = await self._perform_request(
            method,
            path,
            params=params,
            json=json,
            headers=headers,
            timeout_seconds=timeout_seconds,
        )
        return self._parse_response(response)

    async def _perform_request(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        json: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
        timeout_seconds: int | None = None,
    ) -> AsyncResponse:
        """Send a request, handle one token refresh, log, and validate status."""
        started_at = perf_counter()
        response: AsyncResponse | None = None
        request_url = self._build_url(path)
        request_logged = False

        try:
            response = await self._request_with_current_token(
                method,
                path,
                params=params,
                json=json,
                headers=headers,
                timeout_seconds=timeout_seconds,
            )

            if response.status_code == HTTP_UNAUTHORIZED:
                self._logger.info("Access token rejected; refreshing token and retrying.")
                self._token_manager.get_access_token(force_refresh=True)
                response = await self._request_with_current_token(
                    method,
                    path,
                    params=params,
                    json=json,
                    headers=headers,
                    timeout_seconds=timeout_seconds,
                )

            self._log_request(method, request_url, response, started_at)
            request_logged = True
            self._raise_for_status(response)
            return response
        except Exception as exc:
            if not request_logged:
                self._log_request(method, request_url, response, started_at)
            log_exception(
                self._logger,
                exc=exc,
                request_url=response.url if response is not None else request_url,
                http_status=response.status_code if response is not None else None,
                response_body=(
                    self._safe_response_body(response) if response is not None else None
                ),
            )
            raise

    async def _request_with_current_token(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        json: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
        timeout_seconds: int | None = None,
    ) -> AsyncResponse:
        """Attach the current bearer token and send a retryable request."""
        access_token = self._token_manager.get_access_token()
        self._last_retry_count = 0
        request_headers = {
            "Accept": "application/json",
            "User-Agent": "pyprocore-async/2.2.0",
            "Authorization": f"Bearer {access_token}",
            **dict(headers or {}),
        }
        return await self._send_with_retry(
            method=method.upper(),
            url=self._build_url(path),
            params=params,
            json=json,
            headers=request_headers,
            timeout=timeout_seconds or self._timeout_seconds,
        )

    async def _send_with_retry(
        self,
        *,
        method: str,
        url: str,
        params: Mapping[str, Any] | None,
        json: Mapping[str, Any] | None,
        headers: Mapping[str, str],
        timeout: int,
    ) -> AsyncResponse:
        """Send a request and retry transient failures."""
        last_response: AsyncResponse | None = None
        for attempt in range(1, self._retry_attempts + 1):
            self._last_retry_count = attempt - 1
            try:
                response = await self._transport.request(
                    method=method,
                    url=url,
                    params=params,
                    json=json,
                    headers=headers,
                    timeout=timeout,
                )
            except Exception:
                if attempt >= self._retry_attempts:
                    raise
                await self._sleep_before_retry(attempt)
                continue

            last_response = response
            if response.status_code not in RETRYABLE_STATUS_CODES:
                return response
            if attempt < self._retry_attempts:
                await self._sleep_before_retry(attempt)
                continue
            self._raise_retryable(response)

        if last_response is not None:
            self._raise_retryable(last_response)
        raise TransientAPIError(f"Async Procore request failed for {method} {url}")

    async def _sleep_before_retry(self, attempt: int) -> None:
        """Sleep between retry attempts."""
        if self._retry_sleep_seconds <= 0:
            return
        await asyncio.sleep(min(self._retry_sleep_seconds * (2 ** (attempt - 1)), 10.0))

    def _log_request(
        self,
        method: str,
        request_url: str,
        response: AsyncResponse | None,
        started_at: float,
    ) -> None:
        """Log a completed or failed request without sensitive headers."""
        elapsed_ms = (perf_counter() - started_at) * 1000
        log_api_request(
            self._logger,
            method=method.upper(),
            endpoint=response.url if response is not None else request_url,
            status_code=response.status_code if response is not None else None,
            elapsed_ms=elapsed_ms,
            retry_count=self._last_retry_count,
        )

    def _build_url(self, path: str) -> str:
        """Build a full request URL from an API path or absolute URL."""
        if path.startswith(("http://", "https://")):
            return path
        return urljoin(f"{self._settings.api_base}/", path.lstrip("/"))

    def _raise_retryable(self, response: AsyncResponse) -> None:
        """Raise the correct retryable exception for a response."""
        message = self._response_error_message(response)
        body = self._safe_response_body(response)
        if response.status_code == HTTP_RATE_LIMITED:
            raise RateLimitError(message, status_code=response.status_code, response_body=body)
        raise TransientAPIError(message, status_code=response.status_code, response_body=body)

    def _raise_for_status(self, response: AsyncResponse) -> None:
        """Map unsuccessful responses to SDK exceptions."""
        if response.ok:
            return

        message = self._response_error_message(response)
        body = self._safe_response_body(response)
        if response.status_code == HTTP_UNAUTHORIZED:
            raise AuthenticationError(message)
        if response.status_code == HTTP_FORBIDDEN:
            raise AuthorizationError(message)
        if response.status_code == HTTP_NOT_FOUND:
            raise ResourceNotFoundError(
                message, status_code=response.status_code, response_body=body
            )
        raise ProcoreAPIError(message, status_code=response.status_code, response_body=body)

    @staticmethod
    def _parse_response(response: AsyncResponse) -> Any:
        """Return JSON response data, text, or ``None`` for empty responses."""
        if response.status_code == HTTP_NO_CONTENT:
            return None
        content_type = response.headers.get("Content-Type", "")
        if "application/json" in content_type or response.json_data is not None:
            return response.json()
        if response.content:
            return response.text
        return None

    @staticmethod
    def _safe_response_body(response: AsyncResponse) -> Any:
        """Return a sanitized response body for errors."""
        try:
            return sanitize_log_value(response.json())
        except ValueError:
            return sanitize_log_value(response.text)

    @staticmethod
    def _response_error_message(response: AsyncResponse) -> str:
        """Build a concise message for an unsuccessful Procore response."""
        request_method = response.request.method if response.request else "UNKNOWN"
        return (
            f"Procore API request failed with status {response.status_code} "
            f"for {request_method} {response.url}"
        )

    @staticmethod
    def _next_page(
        response: AsyncResponse,
        current_params: Mapping[str, Any] | None,
    ) -> tuple[str | None, dict[str, Any] | None]:
        """Return the next page path and params from Procore pagination headers."""
        link_header = response.headers.get("Link")
        if link_header:
            next_url = AsyncProcoreClient._next_link_url(link_header)
            if next_url:
                return next_url, None

        next_page = response.headers.get("X-Next-Page")
        if next_page:
            next_page = next_page.strip()
            if next_page:
                params = dict(current_params or {})
                params["page"] = int(next_page) if next_page.isdigit() else next_page
                path_url = (
                    response.request.path_url if response.request is not None else response.url
                )
                return path_url.split("?", 1)[0], params

        return None, None

    @staticmethod
    def _next_link_url(link_header: str) -> str | None:
        """Parse a RFC 5988 Link header and return the rel=next URL."""
        for part in link_header.split(","):
            section = part.strip()
            if 'rel="next"' not in section and "rel=next" not in section:
                continue
            if not section.startswith("<") or ">" not in section:
                continue
            next_url = section[1 : section.index(">")]
            parsed = urlparse(next_url)
            query = parse_qs(parsed.query)
            if parsed.scheme and parsed.netloc:
                return next_url
            if query:
                return next_url
            return next_url
        return None


__all__ = ["AsyncProcoreClient"]
