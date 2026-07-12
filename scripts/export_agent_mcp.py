"""Export discovery-only PyProcore MCP adapter metadata files."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from pyprocore.agent import (
    export_mcp_manifest_json,
    export_mcp_prompts_json,
    export_mcp_resources_json,
    export_mcp_tools_json,
)


def build_parser() -> argparse.ArgumentParser:
    """Build the MCP export script parser."""
    parser = argparse.ArgumentParser(
        description="Export discovery-only MCP metadata for PyProcore agent tools."
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("agent-mcp-output"),
        help="Directory where MCP JSON files should be written.",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON files with two-space indentation.",
    )
    return parser


def main() -> int:
    """Write MCP metadata files and return an exit code."""
    args = build_parser().parse_args()
    output_dir: Path = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    files = {
        "mcp-tools.json": export_mcp_tools_json(pretty=args.pretty),
        "mcp-resources.json": export_mcp_resources_json(pretty=args.pretty),
        "mcp-prompts.json": export_mcp_prompts_json(pretty=args.pretty),
        "mcp-manifest.json": export_mcp_manifest_json(pretty=args.pretty),
    }
    for filename, content in files.items():
        (output_dir / filename).write_text(content + "\n", encoding="utf-8")

    print("PyProcore MCP metadata exported.")
    print(f"Output directory: {output_dir}")
    print("Discovery only: no Procore API calls were made.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
