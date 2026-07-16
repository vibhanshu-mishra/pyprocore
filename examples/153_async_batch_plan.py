"""Build and validate an async batch plan without calling Procore."""

from __future__ import annotations

from pyprocore import build_async_batch_dry_run_manifest, build_async_batch_plan


def main() -> None:
    """Create a placeholder async batch plan and print the dry-run summary."""
    plan = build_async_batch_plan(
        company_id=12345,
        project_ids=[67890, 11111],
        resources=["rfis", "submittals"],
        output_dir="./exports/async-batch/example",
        dry_run=True,
    )
    manifest = build_async_batch_dry_run_manifest(plan)
    print(f"Plan: {manifest.plan_name}")
    print(f"Planned project/resource files: {len(manifest.results)}")
    print("No Procore API calls were made.")


if __name__ == "__main__":
    main()
