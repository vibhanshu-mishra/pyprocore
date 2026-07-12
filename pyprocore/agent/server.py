"""Local HTTP API for PyProcore agent discovery metadata."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import unquote, urlparse

from pyprocore.agent.models import AgentManifest, AgentToolRegistry
from pyprocore.agent.registry import (
    get_agent_registry,
)

DEFAULT_AGENT_API_HOST = "127.0.0.1"
DEFAULT_AGENT_API_PORT = 8765
AGENT_API_SERVICE_NAME = "pyprocore-agent-api"


def _json_bytes(payload: dict[str, Any] | list[Any]) -> bytes:
    """Serialize an API response payload as deterministic JSON bytes."""
    return json.dumps(payload, indent=2, sort_keys=True, default=str).encode("utf-8")


def _service_version() -> str:
    """Return the installed PyProcore version without importing credentials."""
    from pyprocore import __version__

    return __version__


def create_agent_api_handler(
    registry: AgentToolRegistry | None = None,
) -> type[BaseHTTPRequestHandler]:
    """Create a request handler for the local agent discovery API.

    Args:
        registry: Optional static registry to serve. When omitted, the current
            local registry is used.

    Returns:
        A ``BaseHTTPRequestHandler`` subclass suitable for ``ThreadingHTTPServer``.
    """
    active_registry = registry or get_agent_registry()
    tools_by_name = {tool.name: tool for tool in active_registry.tools}

    class AgentAPIHandler(BaseHTTPRequestHandler):
        """HTTP handler for local PyProcore agent discovery endpoints."""

        server_version = AGENT_API_SERVICE_NAME
        protocol_version = "HTTP/1.1"

        def do_GET(self) -> None:
            """Handle GET requests for registry discovery endpoints."""
            path = urlparse(self.path).path
            if path == "/":
                self._send_json(
                    HTTPStatus.OK,
                    {
                        "service": AGENT_API_SERVICE_NAME,
                        "version": _service_version(),
                        "links": {
                            "health": "/health",
                            "manifest": "/agent/manifest",
                            "tools": "/agent/tools",
                        },
                    },
                )
                return

            if path == "/health":
                self._send_json(
                    HTTPStatus.OK,
                    {
                        "status": "ok",
                        "service": AGENT_API_SERVICE_NAME,
                        "version": _service_version(),
                    },
                )
                return

            if path == "/agent/manifest":
                manifest = self._build_manifest()
                self._send_json(HTTPStatus.OK, manifest.model_dump(mode="json"))
                return

            if path == "/agent/tools":
                self._send_json(
                    HTTPStatus.OK,
                    [tool.model_dump(mode="json") for tool in active_registry.tools],
                )
                return

            if path.startswith("/agent/tools/"):
                tool_name = unquote(path.removeprefix("/agent/tools/"))
                self._send_tool(tool_name)
                return

            self._send_not_found(path)

        def do_POST(self) -> None:
            """Handle POST requests for disabled future execution endpoints."""
            path = urlparse(self.path).path
            if path.startswith("/agent/tools/") and path.endswith("/call"):
                tool_name = unquote(path.removeprefix("/agent/tools/").removesuffix("/call"))
                if tool_name not in tools_by_name:
                    self._send_unknown_tool(tool_name)
                    return
                self._send_json(
                    HTTPStatus.NOT_IMPLEMENTED,
                    {
                        "error": "tool_execution_disabled",
                        "message": "Tool execution is not enabled in Phase 7B.",
                        "tool": tool_name,
                    },
                )
                return

            self._send_not_found(path)

        def log_message(self, format: str, *args: object) -> None:
            """Suppress default HTTP request logging for local metadata calls."""
            return

        def _send_tool(self, tool_name: str) -> None:
            """Send one tool response or a JSON not-found response."""
            tool = tools_by_name.get(tool_name)
            if tool is None:
                self._send_unknown_tool(tool_name)
                return
            self._send_json(HTTPStatus.OK, tool.model_dump(mode="json"))

        def _build_manifest(self) -> AgentManifest:
            """Build a manifest payload from the active registry."""
            return AgentManifest(
                package_name="pyprocore",
                package_version=_service_version(),
                registry_version=active_registry.registry_version,
                generated_at=datetime.now(timezone.utc),
                tool_count=active_registry.tool_count,
                tools=list(tools_by_name.values()),
            )

        def _send_unknown_tool(self, tool_name: str) -> None:
            """Send a JSON response for an unknown agent tool."""
            self._send_json(
                HTTPStatus.NOT_FOUND,
                {
                    "error": "tool_not_found",
                    "message": f"Agent tool is not registered: {tool_name}",
                    "tool": tool_name,
                },
            )

        def _send_not_found(self, path: str) -> None:
            """Send a JSON response for an unknown route."""
            self._send_json(
                HTTPStatus.NOT_FOUND,
                {
                    "error": "not_found",
                    "message": f"Route not found: {path}",
                    "path": path,
                },
            )

        def _send_json(
            self,
            status: HTTPStatus,
            payload: dict[str, Any] | list[Any],
        ) -> None:
            """Write a JSON API response."""
            body = _json_bytes(payload)
            self.send_response(status.value)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    return AgentAPIHandler


def run_agent_api_server(
    host: str = DEFAULT_AGENT_API_HOST,
    port: int = DEFAULT_AGENT_API_PORT,
    registry: AgentToolRegistry | None = None,
) -> None:
    """Run the local PyProcore agent discovery API server.

    Args:
        host: Bind host. Defaults to ``127.0.0.1`` for local-only access.
        port: TCP port to bind.
        registry: Optional static registry to serve.
    """
    handler = create_agent_api_handler(registry=registry)
    server = ThreadingHTTPServer((host, port), handler)
    url = f"http://{host}:{server.server_port}"
    print(f"PyProcore agent API server running at {url}")
    print("Discovery only. Tool execution is disabled in Phase 7B.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping PyProcore agent API server.")
    finally:
        server.server_close()
