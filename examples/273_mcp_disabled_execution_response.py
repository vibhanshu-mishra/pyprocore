"""Show the disabled MCP tool-call response.

PyProcore exposes MCP discovery metadata only. Tool calls return a safe disabled
response instead of running SDK operations.
"""

from __future__ import annotations

from pyprocore.mcp import disabled_mcp_execution_response


def main() -> None:
    """Print the disabled-response shape for a sample tool name."""
    response = disabled_mcp_execution_response("procore.example")
    print(response["message"])
    print(f"Execution enabled: {response['safety']['mcp_execution_enabled']}")
    print(f"Live Procore call: {response['safety']['calls_live_procore_api']}")


if __name__ == "__main__":
    main()
