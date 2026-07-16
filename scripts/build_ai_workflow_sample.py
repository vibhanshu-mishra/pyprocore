#!/usr/bin/env python3
"""Build a local Phase 12 AI workflow sample package.

The script uses placeholder data only. It never calls Procore, AI/model APIs,
MCP execution, or vector databases.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from pyprocore.workflows import AiWorkflowInput, write_ai_workflow_package  # noqa: E402


def main() -> int:
    """Build a sample package and return a process exit code."""
    parser = argparse.ArgumentParser(description="Build a local AI workflow sample package.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("examples/generated/ai-workflow-sample"),
        help="Local output directory. Defaults to an ignored examples/generated folder.",
    )
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing files.")
    args = parser.parse_args()

    workflow_input = AiWorkflowInput(
        title="Placeholder RFI Review Package",
        workflow="rfi_review",
        summary="Placeholder local context from a reviewed PyProcore export.",
        records=[
            {"number": "RFI-PLACEHOLDER", "title": "Placeholder detail question"},
        ],
        notes=["Replace placeholder records with reviewed local exports."],
    )
    package = write_ai_workflow_package(
        workflow_input,
        args.output_dir,
        overwrite=args.overwrite,
    )
    print(f"Built local AI workflow sample: {package.manifest_path}")
    print("No Procore or external AI/model calls were made.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
