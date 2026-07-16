#!/usr/bin/env python3
"""Validate a scheduled export plan without calling Procore."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from pyprocore.workflows import load_scheduled_export_plan, validate_scheduled_export_plan


def main() -> int:
    """Validate a local scheduled export plan."""
    parser = argparse.ArgumentParser(description="Validate a scheduled export plan.")
    parser.add_argument("plan_path", type=Path)
    parser.add_argument("--json", dest="json_output", action="store_true")
    args = parser.parse_args()

    report = validate_scheduled_export_plan(load_scheduled_export_plan(args.plan_path))
    if args.json_output:
        print(json.dumps(report.model_dump(mode="json"), indent=2))
    else:
        print(f"Scheduled export plan: {report.plan_name}")
        print(f"Valid: {report.is_valid}")
        for finding in report.findings:
            print(f"- {finding.severity.upper()}: {finding.message}")
    return 0 if report.is_valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
