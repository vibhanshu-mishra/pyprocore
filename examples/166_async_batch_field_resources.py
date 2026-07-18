"""Build a local async batch dry-run for field resources."""

from __future__ import annotations

from pyprocore import build_async_batch_dry_run_manifest, build_async_batch_plan


def main() -> None:
    """Preview a local-only async batch plan with Phase 10D resources."""
    plan = build_async_batch_plan(
        company_id=12345,
        project_ids=[67890],
        resources=["observations", "punch_items", "meetings", "inspections", "incidents"],
        output_dir="./exports/async-field-batch",
        dry_run=True,
    )
    manifest = build_async_batch_dry_run_manifest(plan)
    print("Async batch field-resource dry-run complete.")
    print(f"Planned files: {len(manifest.results)}")
    print("No Procore API calls were made.")


if __name__ == "__main__":
    main()
