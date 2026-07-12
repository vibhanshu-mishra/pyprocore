"""Show the MCP adapter's discovery-only disabled execution response.

This example is safe to run without credentials. It does not call Procore and
does not execute any PyProcore tools.
"""

from __future__ import annotations

import json

from pyprocore.agent import (
    build_mcp_tool_definitions,
    build_mcp_tool_execution_disabled_response,
)


def main() -> None:
    """Print a small MCP discovery summary and disabled call response."""
    tools = build_mcp_tool_definitions()
    print(f"Discovered {len(tools)} MCP-style PyProcore tools.")

    first_tool_name = tools[0]["name"] if tools else "procore.find_rfi"
    print(f"Example tool: {first_tool_name}")

    disabled_response = build_mcp_tool_execution_disabled_response(first_tool_name)
    print("If an MCP client tries to call a tool in Phase 7E, it receives:")
    print(json.dumps(disabled_response, indent=2))


if __name__ == "__main__":
    main()
