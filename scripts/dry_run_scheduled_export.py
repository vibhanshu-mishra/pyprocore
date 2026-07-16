#!/usr/bin/env python3
"""Show a dry-run manifest for a scheduled export plan."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from pyprocore.workflows import explain_scheduled_export_plan, export_plan_to_manifest


def main() -> int:
    """Explain a scheduled export plan without fetching Procore data."""
    parser = argparse.ArgumentParser(description="Dry-run a scheduled export plan.")
    parser.add_argument("plan_path", type=Path)
    parser.add_argument("--json", dest="json_output", action="store_true")
    args = parser.parse_args()

    if args.json_output:
        manifest = export_plan_to_manifest(args.plan_path)
        print(json.dumps(manifest.model_dump(mode="json"), indent=2, default=str))
    else:
        print(explain_scheduled_export_plan(args.plan_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
