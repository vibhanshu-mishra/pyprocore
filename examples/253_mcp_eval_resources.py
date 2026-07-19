"""Inspect local eval suite resources exposed through MCP discovery."""

from pyprocore.mcp import read_mcp_resource_payload


def main() -> None:
    """Print bundled eval suite names from local metadata."""
    payload = read_mcp_resource_payload("pyprocore://evals/suites")
    evals = payload["payload"]
    print(f"Local eval suites: {evals['suite_count']}")
    for suite_name in evals["suites"][:10]:
        print(f"- {suite_name}")
    print("Eval metadata is local and deterministic.")


if __name__ == "__main__":
    main()
