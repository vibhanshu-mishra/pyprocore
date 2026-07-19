"""Inspect AI workflow template metadata exposed through MCP discovery."""

from pyprocore.mcp import read_mcp_resource_payload


def main() -> None:
    """Print local AI workflow template names."""
    payload = read_mcp_resource_payload("pyprocore://ai-workflows/templates")
    print(f"Mode: {payload['payload']['mode']}")
    for template in payload["payload"]["templates"]:
        print(f"- {template}")
    print("These are model-agnostic local templates. No external model was called.")


if __name__ == "__main__":
    main()
