"""Tests for the local PyProcore agent API server."""

from __future__ import annotations

import json
import subprocess
import sys
import threading
import unittest
from contextlib import AbstractContextManager
from http.server import ThreadingHTTPServer
from io import BytesIO
from pathlib import Path
from types import TracebackType
from typing import Any
from unittest.mock import patch
from urllib import request
from urllib.error import HTTPError

from pyprocore import app
from pyprocore.agent import create_agent_api_handler
from pyprocore.agent.server import AGENT_API_SERVICE_NAME
from pyprocore.core.exceptions import ValidationError

PROJECT_ROOT = Path(__file__).resolve().parents[1]


class RunningAgentAPIServer(AbstractContextManager["RunningAgentAPIServer"]):
    """Context manager for a short-lived local agent API server."""

    def __init__(self) -> None:
        """Initialize the local test server."""
        try:
            self.server = ThreadingHTTPServer(("127.0.0.1", 0), create_agent_api_handler())
        except PermissionError as exc:
            raise unittest.SkipTest("Local loopback socket binding is not permitted.") from exc
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)

    @property
    def base_url(self) -> str:
        """Return the local base URL for the running server."""
        return f"http://127.0.0.1:{self.server.server_port}"

    def __enter__(self) -> "RunningAgentAPIServer":
        """Start the local test server."""
        self.thread.start()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Stop the local test server."""
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)


def read_json(url: str, *, method: str = "GET") -> tuple[int, dict[str, Any] | list[Any]]:
    """Read a JSON response from the local test server."""
    api_request = request.Request(url, method=method)
    try:
        with request.urlopen(api_request, timeout=5) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        return exc.code, json.loads(exc.read().decode("utf-8"))


def dispatch_handler(
    path: str,
    *,
    method: str = "GET",
) -> tuple[int, dict[str, str], dict[str, Any] | list[Any]]:
    """Dispatch a request handler without opening a local socket."""
    handler_cls = create_agent_api_handler()
    handler = handler_cls.__new__(handler_cls)
    handler.path = path
    handler.wfile = BytesIO()

    captured_status = 0
    captured_headers: dict[str, str] = {}

    def send_response(status: int) -> None:
        nonlocal captured_status
        captured_status = status

    def send_header(name: str, value: str) -> None:
        captured_headers[name] = value

    handler.send_response = send_response  # type: ignore[method-assign]
    handler.send_header = send_header  # type: ignore[method-assign]
    handler.end_headers = lambda: None  # type: ignore[method-assign]

    if method == "GET":
        handler.do_GET()
    elif method == "POST":
        handler.do_POST()
    else:
        raise AssertionError(f"Unsupported test method: {method}")

    payload = json.loads(handler.wfile.getvalue().decode("utf-8"))
    return captured_status, captured_headers, payload


class AgentAPIServerTestCase(unittest.TestCase):
    """Validate local agent API discovery endpoints and CLI safety."""

    def test_health_endpoint_works(self) -> None:
        """The health endpoint should return service status."""
        status, headers, payload = dispatch_handler("/health")

        self.assertEqual(status, 200)
        self.assertEqual(headers["Content-Type"], "application/json")
        self.assertIsInstance(payload, dict)
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["service"], AGENT_API_SERVICE_NAME)
        self.assertEqual(payload["version"], "2.1.0")

    def test_manifest_tools_and_tool_lookup_work(self) -> None:
        """The server should expose manifest, tools, and dotted tool lookup."""
        manifest_status, _, manifest = dispatch_handler("/agent/manifest")
        tools_status, _, tools = dispatch_handler("/agent/tools")
        tool_status, _, tool = dispatch_handler("/agent/tools/procore.find_rfi")

        self.assertEqual(manifest_status, 200)
        self.assertIsInstance(manifest, dict)
        self.assertEqual(manifest["package_name"], "pyprocore")
        self.assertEqual(manifest["package_version"], "2.1.0")

        self.assertEqual(tools_status, 200)
        self.assertIsInstance(tools, list)
        self.assertTrue(any(item["name"] == "procore.find_rfi" for item in tools))

        self.assertEqual(tool_status, 200)
        self.assertIsInstance(tool, dict)
        self.assertEqual(tool["name"], "procore.find_rfi")

    def test_root_unknown_route_and_unknown_tool_return_json(self) -> None:
        """Root should link endpoints and missing resources should return JSON."""
        root_status, _, root = dispatch_handler("/")
        route_status, _, route = dispatch_handler("/missing")
        tool_status, _, tool = dispatch_handler("/agent/tools/procore.missing")

        self.assertEqual(root_status, 200)
        self.assertIsInstance(root, dict)
        self.assertEqual(root["service"], AGENT_API_SERVICE_NAME)
        self.assertIn("manifest", root["links"])

        self.assertEqual(route_status, 404)
        self.assertIsInstance(route, dict)
        self.assertEqual(route["error"], "not_found")

        self.assertEqual(tool_status, 404)
        self.assertIsInstance(tool, dict)
        self.assertEqual(tool["error"], "tool_not_found")

    def test_tool_call_is_explicitly_disabled(self) -> None:
        """The Phase 7B server should not execute tools."""
        status, _, payload = dispatch_handler(
            "/agent/tools/procore.find_rfi/call",
            method="POST",
        )

        self.assertEqual(status, 501)
        self.assertIsInstance(payload, dict)
        self.assertEqual(payload["error"], "tool_execution_disabled")
        self.assertEqual(payload["tool"], "procore.find_rfi")

    def test_post_unknown_tool_and_route_return_json(self) -> None:
        """POST requests should return JSON for unknown tools and routes."""
        tool_status, _, tool_payload = dispatch_handler(
            "/agent/tools/procore.missing/call",
            method="POST",
        )
        route_status, _, route_payload = dispatch_handler("/agent/unknown", method="POST")

        self.assertEqual(tool_status, 404)
        self.assertIsInstance(tool_payload, dict)
        self.assertEqual(tool_payload["error"], "tool_not_found")

        self.assertEqual(route_status, 404)
        self.assertIsInstance(route_payload, dict)
        self.assertEqual(route_payload["error"], "not_found")

    def test_server_does_not_require_credentials_or_live_api(self) -> None:
        """Discovery endpoints should not need config or live Procore access."""
        status, _, payload = dispatch_handler("/agent/tools")

        self.assertEqual(status, 200)
        self.assertIsInstance(payload, list)

    def test_real_local_server_starts_when_environment_allows_sockets(self) -> None:
        """The server should start on a random local port when sockets are allowed."""
        with RunningAgentAPIServer() as server:
            status, payload = read_json(f"{server.base_url}/health")

        self.assertEqual(status, 200)
        self.assertIsInstance(payload, dict)
        self.assertEqual(payload["status"], "ok")

    def test_cli_parser_includes_agent_serve(self) -> None:
        """The CLI parser should include agent serve options."""
        parser = app.build_parser()
        args = parser.parse_args(["agent", "serve", "--host", "127.0.0.1", "--port", "8765"])

        self.assertEqual(args.command, "agent")
        self.assertEqual(args.agent_command, "serve")
        self.assertEqual(args.host, "127.0.0.1")
        self.assertEqual(args.port, 8765)
        self.assertFalse(args.allow_public_bind)

    def test_public_bind_requires_explicit_flag(self) -> None:
        """Binding to 0.0.0.0 should fail without explicit opt-in."""
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pyprocore.app",
                "agent",
                "serve",
                "--host",
                "0.0.0.0",
            ],
            cwd=PROJECT_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("allow-public-bind", result.stdout)

    def test_run_command_agent_serve_branches(self) -> None:
        """Agent serve command dispatch should enforce public-bind safety."""
        parser = app.build_parser()

        local_args = parser.parse_args(["agent", "serve"])
        with patch("pyprocore.app.run_agent_api_server", return_value=None) as run_server:
            self.assertIsNone(app.run_command(local_args))
        run_server.assert_called_once_with(host="127.0.0.1", port=8765)

        public_args = parser.parse_args(
            ["agent", "serve", "--host", "0.0.0.0", "--allow-public-bind"]
        )
        with patch("pyprocore.app.run_agent_api_server", return_value=None) as run_server:
            self.assertIsNone(app.run_command(public_args))
        run_server.assert_called_once_with(host="0.0.0.0", port=8765)

        blocked_args = parser.parse_args(["agent", "serve", "--host", "0.0.0.0"])
        with self.assertRaises(ValidationError):
            app.run_command(blocked_args)

        self.assertFalse(app._requires_public_bind("localhost"))
        self.assertFalse(app._requires_public_bind("127.0.0.1"))
        self.assertTrue(app._requires_public_bind("0.0.0.0"))
        self.assertTrue(app._requires_public_bind("example.com"))

    def test_examples_and_docs_are_linked(self) -> None:
        """Phase 7B example and docs should exist and be linked."""
        for relative_path in (
            "examples/55_agent_api_server.py",
            "docs/recipes/run-local-agent-api-server.md",
            "pyprocore/agent/server.py",
        ):
            self.assertTrue((PROJECT_ROOT / relative_path).exists(), relative_path)

        readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
        docs = (PROJECT_ROOT / "docs/agent-api.md").read_text(encoding="utf-8")
        mkdocs = (PROJECT_ROOT / "mkdocs.yml").read_text(encoding="utf-8")

        self.assertIn("local agent API server", readme)
        self.assertIn("127.0.0.1", docs)
        self.assertIn("run-local-agent-api-server.md", mkdocs)


if __name__ == "__main__":
    unittest.main()
