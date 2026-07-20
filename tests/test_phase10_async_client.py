"""Tests for Phase 10A async client foundation."""

from __future__ import annotations

import importlib
import logging
import unittest
from typing import Any
from unittest.mock import patch

import pyprocore
from pyprocore import AsyncProcore, Procore
from pyprocore.core.async_client import AsyncProcoreClient
from pyprocore.core.async_transport import AsyncResponse, HttpxAsyncTransport, MockAsyncTransport
from pyprocore.core.config import ProcoreSettings
from pyprocore.core.exceptions import (
    AuthenticationError,
    AuthorizationError,
    ConfigurationError,
    ProcoreAPIError,
    RateLimitError,
    ResourceNotFoundError,
    TransientAPIError,
    ValidationError,
)


class FakeTokenManager:
    """Token manager test double that never talks to Procore."""

    def __init__(self) -> None:
        """Initialize token state."""
        self.token = "secret-access-token"
        self.force_refresh_calls = 0

    def get_access_token(self, force_refresh: bool = False) -> str:
        """Return a token and record forced refreshes."""
        if force_refresh:
            self.force_refresh_calls += 1
            self.token = "refreshed-secret-access-token"
        return self.token


def settings() -> ProcoreSettings:
    """Return local test settings."""
    return ProcoreSettings(
        client_id="client-id",
        client_secret="client-secret",
        redirect_uri="http://localhost/callback",
        login_url="https://login.example.com",
        api_base="https://api.example.com",
        company_id=123,
    )


def json_response(
    status_code: int,
    payload: Any,
    *,
    headers: dict[str, str] | None = None,
    url: str = "https://api.example.com/rest/v1.0/example",
) -> AsyncResponse:
    """Build a JSON async response."""
    return AsyncResponse(
        status_code=status_code,
        url=url,
        headers={"Content-Type": "application/json", **dict(headers or {})},
        json_data=payload,
        content=b"{}",
    )


def text_response(
    status_code: int,
    text: str,
    *,
    headers: dict[str, str] | None = None,
    url: str = "https://api.example.com/rest/v1.0/example",
) -> AsyncResponse:
    """Build a text async response."""
    return AsyncResponse(
        status_code=status_code,
        url=url,
        headers={"Content-Type": "text/plain", **dict(headers or {})},
        text=text,
        content=text.encode("utf-8"),
    )


class Phase10AsyncClientTestCase(unittest.IsolatedAsyncioTestCase):
    """Validate async client behavior with local mock transports only."""

    async def asyncTearDown(self) -> None:
        """Avoid leaking handlers between async tests."""
        logger = logging.getLogger("procore_sdk.async_client")
        for handler in list(logger.handlers):
            handler.close()
            logger.removeHandler(handler)

    def build_client(
        self,
        responses: list[AsyncResponse],
    ) -> tuple[AsyncProcore, MockAsyncTransport, FakeTokenManager]:
        """Build an async root client with mock transport."""
        transport = MockAsyncTransport(responses)
        token_manager = FakeTokenManager()
        client = AsyncProcore(
            settings=settings(),
            token_manager=token_manager,  # type: ignore[arg-type]
            transport=transport,
            retry_sleep_seconds=0,
        )
        return client, transport, token_manager

    async def test_async_context_manager_closes_transport(self) -> None:
        """AsyncProcore should support async context manager usage."""
        client, transport, _ = self.build_client([])

        async with client:
            self.assertFalse(transport.closed)

        self.assertTrue(transport.closed)

    async def test_list_companies_uses_bearer_auth_without_logging_token(self) -> None:
        """Async requests should attach bearer auth but avoid logging raw tokens."""
        client, transport, _ = self.build_client(
            [json_response(200, [{"id": 1, "name": "Company"}])]
        )

        with self.assertLogs("procore_sdk.async_client", level="INFO") as logs:
            companies = await client.list_companies()

        self.assertEqual(companies[0].name, "Company")
        self.assertEqual(
            transport.requests[0].headers["Authorization"], "Bearer secret-access-token"
        )
        self.assertNotIn("secret-access-token", "\n".join(logs.output))

    async def test_401_refreshes_access_token_once(self) -> None:
        """A 401 should force refresh and retry once."""
        client, transport, token_manager = self.build_client(
            [
                json_response(401, {"error": "expired"}),
                json_response(200, [{"id": 1, "name": "Company"}]),
            ]
        )

        companies = await client.list_companies()

        self.assertEqual(companies[0].id, 1)
        self.assertEqual(token_manager.force_refresh_calls, 1)
        self.assertEqual(len(transport.requests), 2)
        self.assertIn(
            "refreshed-secret-access-token", transport.requests[1].headers["Authorization"]
        )

    async def test_pagination_collects_all_pages(self) -> None:
        """Async get_all should follow Procore X-Next-Page pagination."""
        client, transport, _ = self.build_client(
            [
                json_response(
                    200,
                    [{"id": 1, "name": "One"}],
                    headers={"X-Next-Page": "2"},
                    url="https://api.example.com/rest/v1.0/companies",
                ),
                json_response(200, [{"id": 2, "name": "Two"}]),
            ]
        )

        companies = await client.list_companies()

        self.assertEqual([company.id for company in companies], [1, 2])
        self.assertEqual(transport.requests[1].params, {"page": 2})

    async def test_link_header_pagination_collects_all_pages(self) -> None:
        """Async get_all should follow RFC 5988 Link pagination."""
        client, transport, _ = self.build_client(
            [
                json_response(
                    200,
                    [{"id": 1, "name": "One"}],
                    headers={
                        "Link": (
                            "<https://api.example.com/rest/v1.0/companies?page=2>; " 'rel="next"'
                        )
                    },
                    url="https://api.example.com/rest/v1.0/companies",
                ),
                json_response(200, [{"id": 2, "name": "Two"}]),
            ]
        )

        companies = await client.list_companies()

        self.assertEqual([company.id for company in companies], [1, 2])
        self.assertEqual(
            transport.requests[1].url, "https://api.example.com/rest/v1.0/companies?page=2"
        )

    async def test_pagination_accepts_wrapped_single_object_pages(self) -> None:
        """Async get_all should collect non-list page payloads."""
        transport = MockAsyncTransport(
            [
                json_response(
                    200,
                    {"id": 1, "name": "Wrapped"},
                    headers={"X-Next-Page": "last"},
                    url="https://api.example.com/rest/v1.0/companies",
                ),
                json_response(200, {"data": [{"id": 2, "name": "Data"}]}),
            ]
        )
        http_client = AsyncProcoreClient(
            settings=settings(),
            token_manager=FakeTokenManager(),  # type: ignore[arg-type]
            transport=transport,
            retry_sleep_seconds=0,
        )

        pages = await http_client.get_all("/rest/v1.0/companies")

        self.assertEqual(pages[0]["id"], 1)
        self.assertEqual(pages[1]["data"][0]["id"], 2)

    async def test_retry_transient_failure_then_success(self) -> None:
        """Transient async failures should be retried."""
        client, transport, _ = self.build_client(
            [
                json_response(500, {"error": "temporary"}),
                json_response(200, [{"id": 1, "name": "Company"}]),
            ]
        )

        companies = await client.list_companies()

        self.assertEqual(companies[0].id, 1)
        self.assertEqual(len(transport.requests), 2)

    async def test_retry_transient_failure_raises_after_attempts(self) -> None:
        """Repeated transient failures should raise SDK transient errors."""
        http_client = AsyncProcoreClient(
            settings=settings(),
            token_manager=FakeTokenManager(),  # type: ignore[arg-type]
            transport=MockAsyncTransport(
                [
                    json_response(500, {"error": "one"}),
                    json_response(500, {"error": "two"}),
                ]
            ),
            retry_attempts=2,
            retry_sleep_seconds=0,
        )

        with self.assertRaises(TransientAPIError):
            await http_client.get("/rest/v1.0/companies")

    async def test_retry_transport_exception_then_success(self) -> None:
        """Transport exceptions should be retried before surfacing."""

        class FlakyTransport(MockAsyncTransport):
            """Raise once, then return a normal queued response."""

            def __init__(self) -> None:
                super().__init__([json_response(200, [{"id": 1, "name": "Company"}])])
                self.calls = 0

            async def request(self, **kwargs: Any) -> AsyncResponse:
                self.calls += 1
                if self.calls == 1:
                    raise OSError("temporary network failure")
                return await super().request(**kwargs)

        transport = FlakyTransport()
        http_client = AsyncProcoreClient(
            settings=settings(),
            token_manager=FakeTokenManager(),  # type: ignore[arg-type]
            transport=transport,
            retry_attempts=2,
            retry_sleep_seconds=0,
        )

        response = await http_client.get("/rest/v1.0/companies")

        self.assertEqual(response[0]["id"], 1)
        self.assertEqual(transport.calls, 2)

    async def test_error_mapping_and_redaction(self) -> None:
        """Async errors should map status codes and redact sensitive response bodies."""
        http_client = AsyncProcoreClient(
            settings=settings(),
            token_manager=FakeTokenManager(),  # type: ignore[arg-type]
            transport=MockAsyncTransport(
                [
                    json_response(
                        403,
                        {"access_token": "secret-access-token", "error": "forbidden"},
                    )
                ]
            ),
            retry_sleep_seconds=0,
        )

        with self.assertLogs("procore_sdk.async_client", level="ERROR") as logs:
            with self.assertRaises(AuthorizationError):
                await http_client.get("/rest/v1.0/companies")

        output = "\n".join(logs.output)
        self.assertIn("[REDACTED]", output)
        self.assertNotIn("secret-access-token", output)

    async def test_404_maps_to_resource_not_found(self) -> None:
        """404 responses should map to ResourceNotFoundError."""
        http_client = AsyncProcoreClient(
            settings=settings(),
            token_manager=FakeTokenManager(),  # type: ignore[arg-type]
            transport=MockAsyncTransport([json_response(404, {"error": "missing"})]),
            retry_sleep_seconds=0,
        )

        with self.assertRaises(ResourceNotFoundError):
            await http_client.get("/rest/v1.0/missing")

    async def test_401_after_refresh_maps_to_authentication_error(self) -> None:
        """A repeated 401 should raise AuthenticationError after one refresh."""
        http_client = AsyncProcoreClient(
            settings=settings(),
            token_manager=FakeTokenManager(),  # type: ignore[arg-type]
            transport=MockAsyncTransport(
                [
                    json_response(401, {"error": "expired"}),
                    json_response(401, {"error": "still expired"}),
                ]
            ),
            retry_sleep_seconds=0,
        )

        with self.assertRaises(AuthenticationError):
            await http_client.get("/rest/v1.0/companies")

    async def test_429_maps_to_rate_limit_error(self) -> None:
        """Repeated 429 responses should map to RateLimitError."""
        http_client = AsyncProcoreClient(
            settings=settings(),
            token_manager=FakeTokenManager(),  # type: ignore[arg-type]
            transport=MockAsyncTransport([json_response(429, {"error": "slow down"})]),
            retry_attempts=1,
            retry_sleep_seconds=0,
        )

        with self.assertRaises(RateLimitError):
            await http_client.get("/rest/v1.0/companies")

    async def test_generic_error_maps_to_procore_api_error_with_text_body(self) -> None:
        """Non-special error statuses should preserve sanitized text body context."""
        http_client = AsyncProcoreClient(
            settings=settings(),
            token_manager=FakeTokenManager(),  # type: ignore[arg-type]
            transport=MockAsyncTransport([text_response(422, "invalid request")]),
            retry_sleep_seconds=0,
        )

        with self.assertRaises(ProcoreAPIError) as error:
            await http_client.get("/rest/v1.0/companies")

        self.assertEqual(error.exception.response_body, "invalid request")

    async def test_parse_response_handles_text_and_no_content(self) -> None:
        """Async request parsing should handle text and 204 responses."""
        http_client = AsyncProcoreClient(
            settings=settings(),
            token_manager=FakeTokenManager(),  # type: ignore[arg-type]
            transport=MockAsyncTransport(
                [
                    text_response(200, "plain response"),
                    AsyncResponse(status_code=204, url="https://api.example.com/rest/v1.0/empty"),
                    AsyncResponse(status_code=200, url="https://api.example.com/rest/v1.0/empty"),
                ]
            ),
            retry_sleep_seconds=0,
        )

        self.assertEqual(await http_client.get("/rest/v1.0/text"), "plain response")
        self.assertIsNone(await http_client.get("/rest/v1.0/empty"))
        self.assertIsNone(await http_client.get("/rest/v1.0/also-empty"))

    async def test_request_accepts_json_headers_and_timeout(self) -> None:
        """Low-level request should pass JSON, custom headers, and timeout through."""
        transport = MockAsyncTransport([json_response(200, {"ok": True})])
        http_client = AsyncProcoreClient(
            settings=settings(),
            token_manager=FakeTokenManager(),  # type: ignore[arg-type]
            transport=transport,
            retry_sleep_seconds=0,
        )

        response = await http_client.request(
            "post",
            "https://api.example.com/rest/v1.0/absolute",
            json={"dry_run": True},
            headers={"X-Test": "yes"},
            timeout_seconds=7,
        )

        self.assertEqual(response, {"ok": True})
        self.assertEqual(transport.requests[0].method, "POST")
        self.assertEqual(transport.requests[0].json, {"dry_run": True})
        self.assertEqual(transport.requests[0].headers["X-Test"], "yes")
        self.assertEqual(transport.requests[0].timeout, 7)

    async def test_initial_resource_coverage_returns_typed_models(self) -> None:
        """Phase 10A should cover the initial read resource set."""
        client, transport, _ = self.build_client(
            [
                json_response(200, [{"id": 10, "name": "Project"}]),
                json_response(200, [{"id": 20, "subject": "RFI"}]),
                json_response(200, {"id": 21, "subject": "RFI detail"}),
                json_response(200, [{"id": 30, "title": "Submittal"}]),
                json_response(200, {"id": 31, "title": "Submittal detail"}),
                json_response(200, [{"files": [{"id": 40, "name": "Document"}]}]),
                json_response(200, [{"id": 50, "name": "Area"}]),
                json_response(200, [{"id": 51, "title": "Drawing"}]),
                json_response(200, [{"id": 60, "number": "01 00 00", "description": "Spec"}]),
            ]
        )

        projects = await client.list_projects(123)
        rfis = await client.list_rfis(123, 456)
        rfi = await client.get_rfi(123, 456, 20)
        submittals = await client.list_submittals(123, 456)
        submittal = await client.get_submittal(123, 456, 30)
        documents = await client.list_documents(123, 456)
        areas = await client.list_drawing_areas(123, 456)
        drawings = await client.list_drawings(123, 456, drawing_area_id=50)
        sections = await client.list_specification_sections(123, 456)

        self.assertEqual(projects[0].name, "Project")
        self.assertEqual(rfis[0].id, 20)
        self.assertEqual(rfi.id, 21)
        self.assertEqual(submittals[0].id, 30)
        self.assertEqual(submittal.id, 31)
        self.assertEqual(documents[0].id, 40)
        self.assertEqual(areas[0].id, 50)
        self.assertEqual(drawings[0].id, 51)
        self.assertEqual(sections[0].number, "01 00 00")
        self.assertEqual(transport.requests[1].headers["Procore-Company-Id"], "123")

    async def test_list_drawings_without_area_lists_across_areas(self) -> None:
        """Async drawings should support the user-friendly across-areas path."""
        client, _, _ = self.build_client(
            [
                json_response(200, [{"id": 50, "name": "Area A"}, {"id": 51, "name": "Area B"}]),
                json_response(200, [{"id": 60, "title": "A-100"}]),
                json_response(200, [{"id": 61, "title": "S-200"}]),
            ]
        )

        drawings = await client.drawings.list(123, 456)

        self.assertEqual([drawing.id for drawing in drawings], [60, 61])

    async def test_list_drawings_skips_areas_without_ids(self) -> None:
        """Drawing aggregation should ignore malformed areas without IDs."""
        client, transport, _ = self.build_client(
            [
                json_response(200, [{"name": "No ID"}, {"id": 51, "name": "Area B"}]),
                json_response(200, [{"id": 61, "title": "S-200"}]),
            ]
        )

        drawings = await client.list_drawings(123, 456)

        self.assertEqual([drawing.id for drawing in drawings], [61])
        self.assertEqual(len(transport.requests), 2)

    async def test_grouped_clients_delegate_to_root_methods(self) -> None:
        """Object client groups should expose async dot-notation access."""
        client, _, _ = self.build_client(
            [
                json_response(200, [{"id": 1, "name": "Company"}]),
                json_response(200, [{"id": 2, "name": "Project"}]),
                json_response(200, [{"id": 3, "subject": "RFI"}]),
            ]
        )

        companies = await client.companies.list()
        projects = await client.projects.list(123)
        rfis = await client.rfis.list(123, 456)

        self.assertEqual(companies[0].id, 1)
        self.assertEqual(projects[0].id, 2)
        self.assertEqual(rfis[0].id, 3)

    async def test_grouped_clients_cover_detail_and_secondary_resources(self) -> None:
        """Grouped async clients should expose detail and secondary resource helpers."""
        client, _, _ = self.build_client(
            [
                json_response(200, {"id": 10, "subject": "RFI"}),
                json_response(200, [{"id": 20, "title": "Submittal"}]),
                json_response(200, {"id": 21, "title": "Submittal detail"}),
                json_response(200, [{"files": [{"id": 30, "name": "Document"}]}]),
                json_response(200, [{"id": 40, "name": "Area"}]),
                json_response(200, [{"id": 50, "number": "01 00 00", "description": "Spec"}]),
            ]
        )

        rfi = await client.rfis.get(123, 456, 10)
        submittals = await client.submittals.list(123, 456)
        submittal = await client.submittals.get(123, 456, 21)
        documents = await client.documents.list(123, 456, folder_id=7)
        areas = await client.drawings.list_areas(123, 456)
        specs = await client.specifications.list_sections(123, 456)

        self.assertEqual(rfi.id, 10)
        self.assertEqual(submittals[0].id, 20)
        self.assertEqual(submittal.id, 21)
        self.assertEqual(documents[0].id, 30)
        self.assertEqual(areas[0].id, 40)
        self.assertEqual(specs[0].number, "01 00 00")

    async def test_wrapped_and_nested_response_helpers(self) -> None:
        """AsyncProcore should support common wrapped response shapes."""
        client = AsyncProcore(
            settings=settings(),
            token_manager=FakeTokenManager(),  # type: ignore[arg-type]
            transport=MockAsyncTransport([]),
            retry_sleep_seconds=0,
        )

        item_records = client._extract_items({"items": [{"id": 1, "name": "Item"}]})
        result_records = client._extract_items({"results": [{"id": 2, "name": "Result"}]})
        empty_records = client._extract_items("not a mapping")
        nested_records = client._extract_nested(
            [{"files": "not a list"}, {"id": 3, "name": "Direct document"}],
            "files",
        )

        self.assertEqual(item_records[0]["id"], 1)
        self.assertEqual(result_records[0]["id"], 2)
        self.assertEqual(empty_records, [])
        self.assertEqual(nested_records[0]["id"], 3)

    async def test_expect_object_rejects_non_object_detail_response(self) -> None:
        """Detail helpers should fail clearly when Procore returns a non-object."""
        client, _, _ = self.build_client([json_response(200, [{"id": 10}])])

        with self.assertRaisesRegex(ValidationError, "Expected Procore RFI"):
            await client.get_rfi(123, 456, 10)

    async def test_mock_transport_fails_clearly_without_queued_response(self) -> None:
        """Mock transport should never silently make network calls."""
        transport = MockAsyncTransport()

        with self.assertRaisesRegex(AssertionError, "No mock async response queued"):
            await transport.request(
                method="GET",
                url="https://api.example.com/rest/v1.0/none",
            )

    async def test_httpx_transport_adapts_json_response_and_closes(self) -> None:
        """The optional httpx adapter should convert responses into AsyncResponse."""

        class FakeRequest:
            url = "https://api.example.com/rest/v1.0/companies"

        class FakeResponse:
            status_code = 200
            url = "https://api.example.com/rest/v1.0/companies"
            headers = {"Content-Type": "application/json"}
            text = '{"ok": true}'
            content = b'{"ok": true}'
            request = FakeRequest()

            def json(self) -> dict[str, bool]:
                return {"ok": True}

        class FakeAsyncClient:
            async def request(self, **_: Any) -> FakeResponse:
                return FakeResponse()

            async def aclose(self) -> None:
                return None

        class FakeHttpxModule:
            AsyncClient = FakeAsyncClient

        with patch("importlib.import_module", return_value=FakeHttpxModule):
            transport = HttpxAsyncTransport()
            async with transport:
                response = await transport.request(
                    method="GET",
                    url="https://api.example.com/rest/v1.0/companies",
                )

        self.assertEqual(response.json(), {"ok": True})
        self.assertEqual(response.request.method, "GET")

    async def test_validation_rejects_invalid_ids(self) -> None:
        """Async resource helpers should validate IDs before requesting."""
        client, transport, _ = self.build_client([])

        with self.assertRaises(ValidationError):
            await client.list_projects(0)
        with self.assertRaises(ValidationError):
            await client.list_documents(123, 456, folder_id=0)
        with self.assertRaises(ValidationError):
            await client.list_drawings(123, 456, drawing_area_id=-1)

        self.assertEqual(transport.requests, [])


class Phase10AsyncSafetyTestCase(unittest.TestCase):
    """Validate Phase 10A package-level safety boundaries."""

    def test_httpx_transport_has_clear_missing_dependency_message(self) -> None:
        """Missing optional async HTTP dependency should fail clearly."""
        real_import = importlib.import_module

        def fake_import(name: str) -> Any:
            if name == "httpx":
                raise ImportError("missing")
            return real_import(name)

        with patch("importlib.import_module", side_effect=fake_import):
            with self.assertRaisesRegex(ConfigurationError, "pyprocore\\[async\\]"):
                HttpxAsyncTransport()

    def test_mock_transport_helpers_and_request_path_url(self) -> None:
        """Mock transport helpers should remain useful for examples and tests."""
        request = pyprocore.AsyncRequest(
            method="GET",
            url="https://api.example.com/rest/v1.0/companies?old=true",
            params={"page": 2, "filters[]": ["a", "b"]},
        )
        response = pyprocore.AsyncResponse(
            status_code=200,
            url="",
            json_data={"ok": True},
        )
        transport = MockAsyncTransport()

        transport.add_response(response)

        self.assertIn("page=2", request.path_url)
        self.assertIn("filters%5B%5D=a", request.path_url)
        self.assertTrue(response.ok)
        self.assertEqual(response.json(), {"ok": True})

    def test_async_exports_are_available_without_replacing_sync_client(self) -> None:
        """AsyncProcore should be additive and the sync Procore client should remain."""
        self.assertEqual(pyprocore.__version__, "2.3.0")
        self.assertIs(pyprocore.AsyncProcore, AsyncProcore)
        self.assertIs(pyprocore.Procore, Procore)

    def test_async_client_does_not_add_write_methods(self) -> None:
        """Phase 10A async client should remain read-oriented."""
        forbidden = ("create", "update", "delete", "post", "put", "patch")
        for name in dir(AsyncProcore):
            if name.startswith("_"):
                continue
            for marker in forbidden:
                self.assertNotIn(marker, name.casefold())

    def test_no_required_ai_or_async_dependencies_were_added(self) -> None:
        """Runtime dependencies should not require AI/vector or async HTTP packages."""
        pyproject = (pyprocore_path() / "pyproject.toml").read_text(encoding="utf-8")
        dependencies_block = pyproject.split("[project.optional-dependencies]", 1)[0]
        for marker in ("httpx", "openai", "anthropic", "langchain", "chromadb", "faiss"):
            self.assertNotIn(marker, dependencies_block.casefold())

    def test_agent_and_mcp_execution_remain_disabled(self) -> None:
        """Phase 10A should not enable agent or MCP execution."""
        from pyprocore.agent import build_mcp_tool_execution_disabled_response

        response = build_mcp_tool_execution_disabled_response("procore.list_projects")

        self.assertFalse(response["metadata"]["execution_enabled"])
        self.assertTrue(response["metadata"]["discovery_only"])


def pyprocore_path() -> Any:
    """Return the repository root path."""
    from pathlib import Path

    return Path(__file__).resolve().parents[1]


if __name__ == "__main__":
    unittest.main()
