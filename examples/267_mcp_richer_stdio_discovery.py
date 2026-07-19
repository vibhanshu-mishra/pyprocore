"""Show the richer Phase 15B stdio discovery payload summary."""

from pyprocore.mcp import build_mcp_stdio_discovery_payload


def main() -> None:
    """Print resource and prompt kind counts from local discovery metadata."""
    discovery = build_mcp_stdio_discovery_payload()
    print("MCP stdio discovery summary:")
    print(f"- resources: {len(discovery['resources'])}")
    print(f"- prompts: {len(discovery['prompts'])}")
    print(f"- resource kinds: {sorted(discovery['resourceKindCounts'])}")
    print(f"- prompt kinds: {sorted(discovery['promptKindCounts'])}")


if __name__ == "__main__":
    main()
