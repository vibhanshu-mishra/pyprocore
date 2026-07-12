"""Export local PyProcore Agent API OpenAPI and schema documents."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def build_parser() -> argparse.ArgumentParser:
    """Build the export script parser."""
    parser = argparse.ArgumentParser(
        description="Export PyProcore Agent API OpenAPI and JSON Schema documents."
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("agent-spec-output"),
        help="Directory where agent-openapi.json and agent-schemas.json are written.",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print exported JSON files.",
    )
    return parser


def main() -> int:
    """Write the local Agent API specification files."""
    from pyprocore.agent import export_agent_openapi_json, export_agent_tool_schemas_json

    args = build_parser().parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    openapi_path = args.output_dir / "agent-openapi.json"
    schemas_path = args.output_dir / "agent-schemas.json"

    openapi_path.write_text(export_agent_openapi_json(pretty=args.pretty), encoding="utf-8")
    schemas_path.write_text(export_agent_tool_schemas_json(pretty=args.pretty), encoding="utf-8")

    print("PyProcore Agent API specification exported.")
    print(f"OpenAPI: {openapi_path}")
    print(f"Schemas: {schemas_path}")
    print("No Procore credentials were loaded and no live API calls were made.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
