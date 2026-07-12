"""Minimal discovery-only MCP-style JSON-RPC stdio adapter.

This adapter intentionally implements only local metadata discovery. Tool calls
always return a disabled execution response and never call Procore.
"""

from __future__ import annotations

import json
import sys
from typing import Any, TextIO

from pyprocore.agent.mcp import (
    build_mcp_prompt_definitions,
    build_mcp_resource_definitions,
    build_mcp_server_info,
    build_mcp_tool_definitions,
    build_mcp_tool_execution_disabled_response,
    read_mcp_resource,
)

JsonObject = dict[str, Any]

JSONRPC_VERSION = "2.0"


def handle_mcp_jsonrpc_request(request: JsonObject) -> JsonObject | None:
    """Handle one JSON-RPC request for the discovery-only MCP adapter.

    Args:
        request: Parsed JSON-RPC request.

    Returns:
        JSON-RPC response object, or ``None`` for notifications.
    """
    request_id = request.get("id")
    method = request.get("method")
    params = request.get("params")

    if request_id is None:
        return None
    if not isinstance(method, str):
        return _jsonrpc_error(request_id, -32600, "Invalid JSON-RPC request.")

    try:
        result = _dispatch_method(method, params if isinstance(params, dict) else {})
    except FileNotFoundError as exc:
        return _jsonrpc_error(request_id, -32004, str(exc))
    except ValueError as exc:
        return _jsonrpc_error(request_id, -32602, str(exc))
    except NotImplementedError:
        return _jsonrpc_error(request_id, -32601, f"Unsupported MCP method: {method}")

    return {"jsonrpc": JSONRPC_VERSION, "id": request_id, "result": result}


def run_mcp_stdio_server(
    *,
    input_stream: TextIO | None = None,
    output_stream: TextIO | None = None,
) -> None:
    """Run a line-delimited JSON-RPC stdio loop.

    Args:
        input_stream: Input stream. Defaults to ``sys.stdin``.
        output_stream: Output stream. Defaults to ``sys.stdout``.
    """
    input_file = input_stream or sys.stdin
    output_file = output_stream or sys.stdout

    for line in input_file:
        line = line.strip()
        if not line:
            continue
        response = _handle_line(line)
        if response is None:
            continue
        output_file.write(json.dumps(response, sort_keys=True) + "\n")
        output_file.flush()


def _handle_line(line: str) -> JsonObject | None:
    """Parse and handle one JSON-RPC line."""
    try:
        request = json.loads(line)
    except json.JSONDecodeError as exc:
        return _jsonrpc_error(None, -32700, f"Invalid JSON: {exc.msg}")

    if not isinstance(request, dict):
        return _jsonrpc_error(None, -32600, "JSON-RPC request must be an object.")
    return handle_mcp_jsonrpc_request(request)


def _dispatch_method(method: str, params: JsonObject) -> JsonObject:
    """Dispatch one supported discovery-only method."""
    if method == "initialize":
        return {
            "protocolVersion": "2024-11-05",
            "serverInfo": build_mcp_server_info(),
            "capabilities": build_mcp_server_info()["capabilities"],
        }
    if method == "ping":
        return {}
    if method == "tools/list":
        return {"tools": build_mcp_tool_definitions()}
    if method == "tools/call":
        name = params.get("name")
        if not isinstance(name, str) or not name:
            raise ValueError("tools/call requires a non-empty string 'name' parameter.")
        return build_mcp_tool_execution_disabled_response(name)
    if method == "resources/list":
        return {"resources": build_mcp_resource_definitions()}
    if method == "resources/read":
        uri = params.get("uri")
        if not isinstance(uri, str) or not uri:
            raise ValueError("resources/read requires a non-empty string 'uri' parameter.")
        return read_mcp_resource(uri)
    if method == "prompts/list":
        return {"prompts": build_mcp_prompt_definitions()}
    raise NotImplementedError


def _jsonrpc_error(
    request_id: str | int | None,
    code: int,
    message: str,
) -> JsonObject:
    """Build a JSON-RPC error response."""
    return {
        "jsonrpc": JSONRPC_VERSION,
        "id": request_id,
        "error": {"code": code, "message": message},
    }
