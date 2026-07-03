"""Unit tests for the reusable Procore HTTP client."""

from __future__ import annotations

import unittest
from unittest.mock import Mock

import requests
from pydantic import SecretStr
from requests import Response
from requests.models import PreparedRequest
from tenacity import wait_none

from core.client import ProcoreClient
from core.config import ProcoreSettings
from core.exceptions import (
    AuthenticationError,
    AuthorizationError,
    ProcoreAPIError,
    RateLimitError,
    ResourceNotFoundError,
)


def settings() -> ProcoreSettings:
    """Return test settings without reading environment variables."""
    return ProcoreSettings(
        client_id="client-id",
        client_secret=SecretStr("client-secret"),
        redirect_uri="http://localhost/callback",
        login_url="https://login.example.com",
        api_base="https://api.example.com",
        company_id=123,
    )


def response(
    status_code: int,
    body: bytes = b'{"ok": true}',
    content_type: str = "application/json",
    method: str = "GET",
    url: str = "https://api.example.com/rest/v1.0/companies",
) -> Response:
    """Build a mocked requests response."""
    prepared = PreparedRequest()
    prepared.prepare(method=method, url=url)

    mocked_response = Response()
    mocked_response.status_code = status_code
    mocked_response._content = body
    mocked_response.headers["Content-Type"] = content_type
    mocked_response.url = url
    mocked_response.request = prepared
    return mocked_response


class ProcoreClientTestCase(unittest.TestCase):
    """Validate ProcoreClient request behavior."""

    def setUp(self) -> None:
        """Create fresh mocks for each test."""
        self.token_manager = Mock()
        self.token_manager.get_access_token.return_value = "token-1"
        self.session = Mock(spec=requests.Session)
        self.session.headers = {}
        self.client = ProcoreClient(
            settings=settings(),
            token_manager=self.token_manager,
            session=self.session,
            timeout_seconds=5,
        )

    def test_get_attaches_authorization_header_and_parses_json(self) -> None:
        """GET requests attach bearer tokens and return parsed JSON."""
        self.session.request.return_value = response(200, b'{"id": 1}')

        result = self.client.get("/rest/v1.0/companies", params={"page": 1})

        self.assertEqual(result, {"id": 1})
        self.session.request.assert_called_once()
        request_kwargs = self.session.request.call_args.kwargs
        self.assertEqual(request_kwargs["method"], "GET")
        self.assertEqual(
            request_kwargs["url"], "https://api.example.com/rest/v1.0/companies"
        )
        self.assertEqual(request_kwargs["headers"]["Authorization"], "Bearer token-1")
        self.assertEqual(request_kwargs["params"], {"page": 1})

    def test_absolute_url_is_not_rebased(self) -> None:
        """Absolute URLs pass through unchanged."""
        self.session.request.return_value = response(200, b'{"ok": true}')

        self.client.get("https://signed.example.com/file.pdf")

        self.assertEqual(
            self.session.request.call_args.kwargs["url"],
            "https://signed.example.com/file.pdf",
        )

    def test_401_refreshes_token_and_retries_once(self) -> None:
        """Unauthorized responses force token refresh and retry."""
        self.token_manager.get_access_token.side_effect = [
            "old-token",
            "new-token",
            "new-token",
        ]
        self.session.request.side_effect = [
            response(401, b'{"error": "expired"}'),
            response(200, b'{"ok": true}'),
        ]

        result = self.client.get("/rest/v1.0/companies")

        self.assertEqual(result, {"ok": True})
        self.token_manager.get_access_token.assert_any_call(force_refresh=True)
        self.assertEqual(self.session.request.call_count, 2)
        self.assertEqual(
            self.session.request.call_args.kwargs["headers"]["Authorization"],
            "Bearer new-token",
        )

    def test_401_after_refresh_raises_authentication_error(self) -> None:
        """Repeated unauthorized responses raise an authentication error."""
        self.session.request.side_effect = [
            response(401, b'{"error": "expired"}'),
            response(401, b'{"error": "still expired"}'),
        ]

        with self.assertRaises(AuthenticationError):
            self.client.get("/rest/v1.0/companies")

    def test_403_raises_authorization_error(self) -> None:
        """Forbidden responses map to AuthorizationError."""
        self.session.request.return_value = response(403, b'{"error": "forbidden"}')

        with self.assertRaises(AuthorizationError):
            self.client.get("/rest/v1.0/companies")

    def test_404_raises_resource_not_found(self) -> None:
        """Not found responses map to ResourceNotFoundError."""
        self.session.request.return_value = response(404, b'{"error": "missing"}')

        with self.assertRaises(ResourceNotFoundError):
            self.client.get("/rest/v1.0/companies/999")

    def test_generic_error_raises_api_error(self) -> None:
        """Non-special unsuccessful responses map to ProcoreAPIError."""
        self.session.request.return_value = response(422, b'{"error": "invalid"}')

        with self.assertRaises(ProcoreAPIError):
            self.client.post("/rest/v1.0/companies", json={"name": "Bad"})

    def test_delete_returns_none_for_204(self) -> None:
        """No-content responses return None."""
        self.session.request.return_value = response(204, b"")

        self.assertIsNone(self.client.delete("/rest/v1.0/companies/1"))

    def test_put_returns_text_for_non_json(self) -> None:
        """Non-JSON responses return text."""
        self.session.request.return_value = response(200, b"accepted", "text/plain")

        self.assertEqual(
            self.client.put("/rest/v1.0/companies/1", data={"name": "A"}),
            "accepted",
        )

    def test_get_all_follows_x_next_page_header(self) -> None:
        """get_all follows Procore X-Next-Page headers."""
        first = response(200, b'[{"id": 1}]')
        first.headers["X-Next-Page"] = "2"
        second = response(200, b'[{"id": 2}]')
        self.session.request.side_effect = [first, second]

        result = self.client.get_all("/rest/v1.0/companies", params={"per_page": 1})

        self.assertEqual(result, [{"id": 1}, {"id": 2}])
        self.assertEqual(self.session.request.call_count, 2)
        self.assertEqual(
            self.session.request.call_args_list[1].kwargs["params"],
            {"per_page": 1, "page": 2},
        )

    def test_get_all_follows_link_header(self) -> None:
        """get_all follows rel=next Link headers."""
        first = response(200, b'[{"id": 1}]')
        first.headers["Link"] = (
            '<https://api.example.com/rest/v1.0/companies?page=2>; rel="next"'
        )
        second = response(200, b'{"id": 2}')
        self.session.request.side_effect = [first, second]

        result = self.client.get_all("/rest/v1.0/companies")

        self.assertEqual(result, [{"id": 1}, {"id": 2}])
        self.assertEqual(
            self.session.request.call_args_list[1].kwargs["url"],
            "https://api.example.com/rest/v1.0/companies?page=2",
        )

    def test_safe_response_body_returns_text_for_non_json_errors(self) -> None:
        """Error body parsing falls back to response text."""
        self.session.request.return_value = response(
            500, b"server exploded", "text/plain"
        )
        original_wait = ProcoreClient._send_with_retry.retry.wait
        ProcoreClient._send_with_retry.retry.wait = wait_none()

        try:
            with self.assertRaises(ProcoreAPIError) as context:
                self.client.get("/rest/v1.0/companies")
        finally:
            ProcoreClient._send_with_retry.retry.wait = original_wait

        self.assertEqual(context.exception.response_body, "server exploded")

    def test_retryable_500_retries_and_then_succeeds(self) -> None:
        """Transient server failures are retried without live HTTP."""
        original_wait = ProcoreClient._send_with_retry.retry.wait
        ProcoreClient._send_with_retry.retry.wait = wait_none()
        self.session.request.side_effect = [
            response(500, b'{"error": "temporary"}'),
            response(200, b'{"ok": true}'),
        ]

        try:
            result = self.client.get("/rest/v1.0/companies")
        finally:
            ProcoreClient._send_with_retry.retry.wait = original_wait

        self.assertEqual(result, {"ok": True})
        self.assertEqual(self.session.request.call_count, 2)

    def test_rate_limit_retries_and_raises_after_attempts(self) -> None:
        """Repeated rate limits raise RateLimitError after retries."""
        original_wait = ProcoreClient._send_with_retry.retry.wait
        ProcoreClient._send_with_retry.retry.wait = wait_none()
        self.session.request.return_value = response(429, b'{"error": "slow down"}')

        try:
            with self.assertRaises(RateLimitError):
                self.client.get("/rest/v1.0/companies")
        finally:
            ProcoreClient._send_with_retry.retry.wait = original_wait

        self.assertEqual(self.session.request.call_count, 3)


if __name__ == "__main__":
    unittest.main()
