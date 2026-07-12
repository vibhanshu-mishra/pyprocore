"""Smoke-test the local PyProcore agent API without calling Procore."""

from __future__ import annotations

import json
import threading
from http.server import ThreadingHTTPServer
from typing import Any
from urllib import request
from urllib.error import HTTPError

from pyprocore.agent import create_agent_api_handler


def _read_json(url: str, *, method: str = "GET") -> tuple[int, dict[str, Any] | list[Any]]:
    """Read a JSON response from the local smoke-test server."""
    api_request = request.Request(url, method=method)
    try:
        with request.urlopen(api_request, timeout=5) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        return exc.code, json.loads(exc.read().decode("utf-8"))


def _assert(condition: bool, message: str) -> None:
    """Raise a clear smoke-test failure when a condition is false."""
    if not condition:
        raise AssertionError(message)


def main() -> int:
    """Run the local agent API smoke test."""
    try:
        server = ThreadingHTTPServer(("127.0.0.1", 0), create_agent_api_handler())
    except PermissionError:
        print("Agent API smoke test skipped: local loopback socket binding is not permitted.")
        return 0
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base_url = f"http://127.0.0.1:{server.server_port}"

    try:
        status, health = _read_json(f"{base_url}/health")
        _assert(status == 200, "Expected /health to return 200.")
        _assert(isinstance(health, dict), "Expected /health to return an object.")
        _assert(health.get("status") == "ok", "Expected health status ok.")

        status, manifest = _read_json(f"{base_url}/agent/manifest")
        _assert(status == 200, "Expected /agent/manifest to return 200.")
        _assert(isinstance(manifest, dict), "Expected manifest to return an object.")
        _assert(manifest.get("package_name") == "pyprocore", "Expected pyprocore manifest.")

        status, tools = _read_json(f"{base_url}/agent/tools")
        _assert(status == 200, "Expected /agent/tools to return 200.")
        _assert(isinstance(tools, list), "Expected tools to return a list.")
        _assert(any(tool["name"] == "procore.find_rfi" for tool in tools), "Missing find_rfi.")

        status, tool = _read_json(f"{base_url}/agent/tools/procore.find_rfi")
        _assert(status == 200, "Expected tool lookup to return 200.")
        _assert(isinstance(tool, dict), "Expected tool lookup to return an object.")
        _assert(tool.get("name") == "procore.find_rfi", "Expected procore.find_rfi.")

        status, openapi = _read_json(f"{base_url}/agent/openapi.json")
        _assert(status == 200, "Expected /agent/openapi.json to return 200.")
        _assert(isinstance(openapi, dict), "Expected OpenAPI to return an object.")
        _assert(openapi.get("openapi") == "3.1.0", "Expected OpenAPI 3.1.0.")

        status, schemas = _read_json(f"{base_url}/agent/schemas")
        _assert(status == 200, "Expected /agent/schemas to return 200.")
        _assert(isinstance(schemas, dict), "Expected schemas to return an object.")
        _assert("procore.find_rfi" in schemas["tools"], "Expected find_rfi schema.")

        status, disabled = _read_json(
            f"{base_url}/agent/tools/procore.find_rfi/call",
            method="POST",
        )
        _assert(status == 501, "Expected disabled tool execution to return 501.")
        _assert(isinstance(disabled, dict), "Expected disabled response object.")
        _assert(
            disabled.get("error") == "tool_execution_disabled",
            "Expected tool_execution_disabled error.",
        )
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)

    print("Agent API smoke test passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
