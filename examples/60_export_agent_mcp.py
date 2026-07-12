"""Export PyProcore agent tools as discovery-only MCP metadata.

This example does not require Procore credentials and does not call the
Procore API. It writes local JSON files that MCP-compatible clients can inspect.
"""

from __future__ import annotations

from pathlib import Path

from pyprocore.agent import (
    export_mcp_manifest_json,
    export_mcp_prompts_json,
    export_mcp_resources_json,
    export_mcp_tools_json,
)


def main() -> None:
    """Write MCP metadata JSON files to a local example output folder."""
    output_dir = Path("example-output/agent-mcp")
    output_dir.mkdir(parents=True, exist_ok=True)

    files = {
        "mcp-tools.json": export_mcp_tools_json(pretty=True),
        "mcp-resources.json": export_mcp_resources_json(pretty=True),
        "mcp-prompts.json": export_mcp_prompts_json(pretty=True),
        "mcp-manifest.json": export_mcp_manifest_json(pretty=True),
    }
    for filename, content in files.items():
        (output_dir / filename).write_text(content + "\n", encoding="utf-8")

    print("MCP metadata exported successfully.")
    print(f"Output folder: {output_dir}")
    print("No Procore credentials were required, and no live API calls were made.")


if __name__ == "__main__":
    main()
