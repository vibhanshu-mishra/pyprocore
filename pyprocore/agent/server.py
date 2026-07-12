"""Local HTTP API for PyProcore agent discovery metadata."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from time import monotonic
from typing import Any
from urllib.parse import unquote, urlparse

from pyprocore.agent.models import AgentManifest, AgentToolRegistry
from pyprocore.agent.openapi import build_agent_openapi_spec, build_agent_tool_schemas
from pyprocore.agent.registry import (
    get_agent_registry,
)
from pyprocore.agent.runs import append_agent_run_event, create_agent_run, redact_path

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
    run_log_dir: Path | str | None = None,
    run_id: str | None = None,
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
    active_run = (
        create_agent_run(
            run_log_dir,
            run_id=run_id,
            source="agent-api-server",
            metadata={"service": AGENT_API_SERVICE_NAME},
        )
        if run_log_dir is not None
        else None
    )

    class AgentAPIHandler(BaseHTTPRequestHandler):
        """HTTP handler for local PyProcore agent discovery endpoints."""

        server_version = AGENT_API_SERVICE_NAME
        protocol_version = "HTTP/1.1"

        def do_GET(self) -> None:
            """Handle GET requests for registry discovery endpoints."""
            self._request_started_at = monotonic()
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
                            "openapi": "/agent/openapi.json",
                            "schemas": "/agent/schemas",
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

            if path == "/agent/openapi.json":
                self._send_json(HTTPStatus.OK, build_agent_openapi_spec(active_registry))
                return

            if path == "/agent/schemas":
                self._send_json(HTTPStatus.OK, build_agent_tool_schemas(active_registry))
                return

            if path.startswith("/agent/tools/"):
                tool_name = unquote(path.removeprefix("/agent/tools/"))
                self._send_tool(tool_name)
                return

            self._send_not_found(path)

        def do_POST(self) -> None:
            """Handle POST requests for disabled future execution endpoints."""
            self._request_started_at = monotonic()
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
            self._log_run_event(status, payload)

        def _log_run_event(
            self,
            status: HTTPStatus,
            payload: dict[str, Any] | list[Any],
        ) -> None:
            """Append a sanitized local run event when logging is enabled."""
            if active_run is None or run_log_dir is None:
                return
            path = urlparse(self.path).path
            started_at = getattr(self, "_request_started_at", None)
            duration_ms = (
                round((monotonic() - started_at) * 1000, 2)
                if isinstance(started_at, float)
                else None
            )
            tool_name = _tool_name_from_path(path)
            error_type = payload.get("error") if isinstance(payload, dict) else None
            append_agent_run_event(
                run_log_dir,
                active_run.run_id,
                method=self.command,
                path=redact_path(path),
                tool_name=tool_name,
                status_code=status.value,
                event_type=_event_type_from_path(path, status.value, error_type),
                request_summary={"path": path, "method": self.command},
                response_summary=_response_summary(payload),
                error_type=error_type,
                duration_ms=duration_ms,
            )

    return AgentAPIHandler


def run_agent_api_server(
    host: str = DEFAULT_AGENT_API_HOST,
    port: int = DEFAULT_AGENT_API_PORT,
    registry: AgentToolRegistry | None = None,
    run_log_dir: Path | str | None = None,
    run_id: str | None = None,
) -> None:
    """Run the local PyProcore agent discovery API server.

    Args:
        host: Bind host. Defaults to ``127.0.0.1`` for local-only access.
        port: TCP port to bind.
        registry: Optional static registry to serve.
    """
    handler = create_agent_api_handler(
        registry=registry,
        run_log_dir=run_log_dir,
        run_id=run_id,
    )
    server = ThreadingHTTPServer((host, port), handler)
    url = f"http://{host}:{server.server_port}"
    print(f"PyProcore agent API server running at {url}")
    print("Discovery only. Tool execution is disabled in Phase 7B.")
    if run_log_dir is not None:
        print(f"Agent run logging enabled: {run_log_dir}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping PyProcore agent API server.")
    finally:
        server.server_close()


def _tool_name_from_path(path: str) -> str | None:
    """Extract a tool name from an Agent API tool path."""
    if not path.startswith("/agent/tools/"):
        return None
    return unquote(path.removeprefix("/agent/tools/").removesuffix("/call"))


def _event_type_from_path(path: str, status_code: int, error_type: str | None) -> str:
    """Return a compact event type for a server response."""
    if error_type:
        return error_type
    if path == "/health":
        return "health"
    if path == "/agent/manifest":
        return "manifest"
    if path == "/agent/tools":
        return "tools"
    if path == "/agent/openapi.json":
        return "openapi"
    if path == "/agent/schemas":
        return "schemas"
    if path.startswith("/agent/tools/") and path.endswith("/call"):
        return "tool_call_disabled" if status_code == 501 else "tool_call"
    if path.startswith("/agent/tools/"):
        return "tool"
    if path == "/":
        return "root"
    return "not_found"


def _response_summary(payload: dict[str, Any] | list[Any]) -> dict[str, Any]:
    """Return a small response summary without raw headers or bodies."""
    if isinstance(payload, list):
        return {"type": "array", "count": len(payload)}
    summary: dict[str, Any] = {"type": "object", "keys": sorted(payload)[:20]}
    for key in ("error", "message", "tool", "status", "service", "version"):
        if key in payload:
            summary[key] = payload[key]
    if "tool_count" in payload:
        summary["tool_count"] = payload["tool_count"]
    return summary
