"""Summarize Phase 15A MCP discovery additions."""

from pyprocore.mcp import build_mcp_discovery_manifest


def main() -> None:
    """Print a compact Phase 15A discovery summary."""
    manifest = build_mcp_discovery_manifest()
    print("Phase 15A MCP discovery summary")
    print(f"- Resources: {len(manifest.resources)}")
    print(f"- Prompt templates: {len(manifest.prompts)}")
    print(f"- Agent tools described: {len(manifest.tools)}")
    print(f"- MCP execution enabled: {manifest.capabilities.safety.mcp_execution_enabled}")
    print("Everything shown here is local metadata only.")


if __name__ == "__main__":
    main()
