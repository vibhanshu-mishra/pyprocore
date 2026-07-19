"""Read local agent schema MCP resources."""

import json

from pyprocore.mcp import read_mcp_resource_payload


def main() -> None:
    """Print a compact summary of local agent schema resources."""
    payload = read_mcp_resource_payload("pyprocore://agent/schemas")
    schema_names = sorted(payload["payload"].get("$defs", {}).keys())
    print("Loaded local agent schema resource.")
    print(f"Schema entries: {len(schema_names)}")
    print(json.dumps(schema_names[:5], indent=2))
    print("No credentials or Procore project IDs were needed.")


if __name__ == "__main__":
    main()
