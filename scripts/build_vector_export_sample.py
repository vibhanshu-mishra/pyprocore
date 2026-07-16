#!/usr/bin/env python3
"""Build a local vector export manifest sample without vector dependencies."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from pyprocore.workflows import build_vector_index_manifest  # noqa: E402


def main() -> int:
    """Build a sample vector export manifest and return an exit code."""
    parser = argparse.ArgumentParser(description="Build a local vector export manifest sample.")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("examples/generated/vector-export-manifest.json"),
        help="Output JSON path. Defaults to an ignored examples/generated folder.",
    )
    args = parser.parse_args()

    manifest = build_vector_index_manifest(
        "Placeholder local context for chunking. Review and redact before indexing.",
        source_name="placeholder-context.md",
        chunk_size=48,
        overlap=8,
        metadata={"project": "PLACEHOLDER_PROJECT"},
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(manifest.model_dump(mode="json"), indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote local vector export sample: {args.output}")
    print("No vector database, Procore API, or external model API was called.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
