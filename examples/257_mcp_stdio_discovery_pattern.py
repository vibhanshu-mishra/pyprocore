"""Build a local stdio-friendly MCP discovery payload."""

import json

from pyprocore.mcp import build_mcp_stdio_discovery_payload


def main() -> None:
    """Print a small part of the stdio discovery payload."""
    payload = build_mcp_stdio_discovery_payload()
    summary = {
        "server": payload["server"]["name"],
        "resources": len(payload["resources"]),
        "prompts": len(payload["prompts"]),
        "execution_enabled": payload["safety"]["mcp_execution_enabled"],
    }
    print(json.dumps(summary, indent=2))
    print("This builds metadata only and does not start a server.")


if __name__ == "__main__":
    main()
