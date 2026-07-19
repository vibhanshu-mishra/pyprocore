"""Inspect model-response fixture MCP resources without calling a model."""

import json

from pyprocore.mcp import read_mcp_resource_payload


def main() -> None:
    """Print the registered local model fixture suite names."""
    payload = read_mcp_resource_payload("pyprocore://evals/model-fixtures")
    print("Model fixture suites:")
    print(json.dumps(payload["payload"]["suites"], indent=2))


if __name__ == "__main__":
    main()
