"""Validate a local plugin manifest against a local trust policy.

This example reads JSON metadata only. It never executes plugin code, installs
packages, imports plugin modules, calls Procore, or fetches remote registries.
"""

from __future__ import annotations

from pathlib import Path

from pyprocore.plugins import (
    load_local_plugin_manifest_file,
    load_trust_policy_from_file,
    trust_report_to_json,
    validate_manifest_trust,
)


def main() -> None:
    """Run a local metadata-only trust validation."""
    root = Path(__file__).resolve().parents[1]
    policy_path = root / "examples" / "configs" / "plugin_trust_policy.json"
    manifest_path = root / "examples" / "plugin_scaffolds" / "trusted_plugin_manifest.json"

    policy = load_trust_policy_from_file(policy_path)
    manifest = load_local_plugin_manifest_file(manifest_path)
    report = validate_manifest_trust(manifest, policy)

    print(trust_report_to_json(report))
    if not report.trusted:
        print("The manifest did not satisfy the local trust policy.")


if __name__ == "__main__":
    main()
