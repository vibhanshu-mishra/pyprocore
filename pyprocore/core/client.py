"""Reusable HTTP client for the Procore REST API."""

from __future__ import annotations

from collections.abc import Mapping
from time import perf_counter
from typing import Any
from urllib.parse import parse_qs, urljoin, urlparse

import requests
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from pyprocore.auth.token_manager import TokenManager
from pyprocore.core.config import ProcoreSettings, get_settings
from pyprocore.core.exceptions import (
    AuthenticationError,
    AuthorizationError,
    ProcoreAPIError,
    RateLimitError,
    ResourceNotFoundError,
    TransientAPIError,
)
from pyprocore.core.logger import get_logger, log_api_request, log_exception

DEFAULT_TIMEOUT_SECONDS = 30
RETRYABLE_STATUS_CODES = {408, 429, 500, 502, 503, 504}
HTTP_NO_CONTENT = 204
HTTP_UNAUTHORIZED = 401
HTTP_FORBIDDEN = 403
HTTP_NOT_FOUND = 404
HTTP_RATE_LIMITED = 429


class ProcoreClient:
    """HTTP client that handles Procore authentication, retries, and errors."""

    def __init__(
        self,
        settings: ProcoreSettings | None = None,
        token_manager: TokenManager | None = None,
        session: requests.Session | None = None,
        timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        """Initialize the Procore HTTP client.

        Args:
            settings: Optional SDK settings. Defaults to environment-backed
                settings.
            token_manager: Optional token manager for bearer tokens.
            session: Optional requests session.
            timeout_seconds: Default timeout for HTTP requests.
        """
        self._settings = settings or get_settings()
        self._token_manager = token_manager or TokenManager(settings=self._settings)
        self._session = session or requests.Session()
        self._timeout_seconds = timeout_seconds
        self._logger = get_logger("client")
        self._current_attempt_count = 0
        self._last_retry_count = 0

        self._session.headers.update(
            {
                "Accept": "application/json",
                "User-Agent": "procore-sdk-python/0.1.0",
            }
        )

    def get(
        self,
        path: str,
        params: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> Any:
        """Send a GET request to Procore."""
        return self.request("GET", path, params=params, headers=headers)

    def get_all(
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
            response = self._perform_request(
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

    def post(
        self,
        path: str,
        json: Mapping[str, Any] | None = None,
        data: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> Any:
        """Send a POST request to Procore."""
        return self.request("POST", path, json=json, data=data, headers=headers)

    def put(
        self,
        path: str,
        json: Mapping[str, Any] | None = None,
        data: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> Any:
        """Send a PUT request to Procore."""
        return self.request("PUT", path, json=json, data=data, headers=headers)

    def delete(
        self,
        path: str,
        params: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> Any:
        """Send a DELETE request to Procore."""
        return self.request("DELETE", path, params=params, headers=headers)

    def request(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        json: Mapping[str, Any] | None = None,
        data: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
        timeout_seconds: int | None = None,
    ) -> Any:
        """Send an authenticated request and parse the response.

        A 401 triggers one forced token refresh and one retry. Transient
        failures are retried by ``tenacity`` before being raised.
        """
        response = self._perform_request(
            method,
            path,
            params=params,
            json=json,
            data=data,
            headers=headers,
            timeout_seconds=timeout_seconds,
        )

        return self._parse_response(response)

    def _perform_request(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        json: Mapping[str, Any] | None = None,
        data: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
        timeout_seconds: int | None = None,
    ) -> requests.Response:
        """Send a request, handle 401 refresh, log, and validate status."""
        started_at = perf_counter()
        response: requests.Response | None = None
        request_url = self._build_url(path)
        request_logged = False

        try:
            response = self._request_with_current_token(
                method,
                path,
                params=params,
                json=json,
                data=data,
                headers=headers,
                timeout_seconds=timeout_seconds,
            )

            if response.status_code == HTTP_UNAUTHORIZED:
                self._logger.info("Access token rejected; refreshing token and retrying.")
                self._token_manager.get_access_token(force_refresh=True)
                response = self._request_with_current_token(
                    method,
                    path,
                    params=params,
                    json=json,
                    data=data,
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

    def _request_with_current_token(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        json: Mapping[str, Any] | None = None,
        data: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
        timeout_seconds: int | None = None,
    ) -> requests.Response:
        """Attach the current bearer token and send a retryable request."""
        access_token = self._token_manager.get_access_token()
        self._current_attempt_count = 0
        self._last_retry_count = 0
        request_headers = {
            "Authorization": f"Bearer {access_token}",
            **dict(headers or {}),
        }

        return self._send_with_retry(
            method=method.upper(),
            url=self._build_url(path),
            params=params,
            json=json,
            data=data,
            headers=request_headers,
            timeout=timeout_seconds or self._timeout_seconds,
        )

    @retry(
        retry=retry_if_exception_type(
            (requests.RequestException, RateLimitError, TransientAPIError)
        ),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        stop=stop_after_attempt(3),
        reraise=True,
    )
    def _send_with_retry(
        self,
        *,
        method: str,
        url: str,
        params: Mapping[str, Any] | None,
        json: Mapping[str, Any] | None,
        data: Mapping[str, Any] | None,
        headers: Mapping[str, str],
        timeout: int,
    ) -> requests.Response:
        """Send an HTTP request and raise retryable failures."""
        self._current_attempt_count += 1
        self._last_retry_count = max(0, self._current_attempt_count - 1)
        response = self._session.request(
            method=method,
            url=url,
            params=params,
            json=json,
            data=data,
            headers=dict(headers),
            timeout=timeout,
        )

        if response.status_code in RETRYABLE_STATUS_CODES:
            error_message = self._response_error_message(response)
            if response.status_code == HTTP_RATE_LIMITED:
                raise RateLimitError(
                    error_message,
                    status_code=response.status_code,
                    response_body=self._safe_response_body(response),
                )
            raise TransientAPIError(
                error_message,
                status_code=response.status_code,
                response_body=self._safe_response_body(response),
            )

        return response

    def _log_request(
        self,
        method: str,
        request_url: str,
        response: requests.Response | None,
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

        base_url = f"{self._settings.api_base}/"
        normalized_path = path.lstrip("/")
        return urljoin(base_url, normalized_path)

    def _raise_for_status(self, response: requests.Response) -> None:
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
                message,
                status_code=response.status_code,
                response_body=body,
            )

        raise ProcoreAPIError(
            message,
            status_code=response.status_code,
            response_body=body,
        )

    @staticmethod
    def _parse_response(response: requests.Response) -> Any:
        """Return JSON response data, text, or ``None`` for empty responses."""
        if response.status_code == HTTP_NO_CONTENT or not response.content:
            return None

        content_type = response.headers.get("Content-Type", "")
        if "application/json" in content_type:
            return response.json()

        return response.text

    @staticmethod
    def _safe_response_body(response: requests.Response) -> Any:
        """Return response body content for errors without assuming JSON."""
        try:
            return response.json()
        except ValueError:
            return response.text

    def _response_error_message(self, response: requests.Response) -> str:
        """Build a concise message for an unsuccessful Procore response."""
        request_method = response.request.method if response.request else "UNKNOWN"
        return (
            f"Procore API request failed with status {response.status_code} "
            f"for {request_method} {response.url}"
        )

    @staticmethod
    def _next_page(
        response: requests.Response,
        current_params: Mapping[str, Any] | None,
    ) -> tuple[str | None, dict[str, Any] | None]:
        """Return the next page path and params from Procore pagination headers."""
        link_header = response.headers.get("Link")
        if link_header:
            next_url = ProcoreClient._next_link_url(link_header)
            if next_url:
                return next_url, None

        next_page = response.headers.get("X-Next-Page")
        if next_page:
            next_page = next_page.strip()
            if next_page:
                params = dict(current_params or {})
                params["page"] = int(next_page) if next_page.isdigit() else next_page
                return response.request.path_url.split("?", 1)[0], params

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
