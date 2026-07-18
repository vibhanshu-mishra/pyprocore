"""Plan an async batch for financial and contract resources without live calls."""

from __future__ import annotations

from pyprocore.workflows import build_async_batch_dry_run_manifest, build_async_batch_plan


def main() -> None:
    """Build and print a local dry-run async batch manifest."""
    plan = build_async_batch_plan(
        company_id=12345,
        project_ids=[67890],
        resources=["change_events", "contracts", "subcontractor_invoices"],
        output_dir="./exports/examples/async-phase10e",
        dry_run=True,
    )
    manifest = build_async_batch_dry_run_manifest(plan)
    print(f"Plan: {manifest.plan_name}")
    print(f"Resources: {', '.join(manifest.resources)}")
    print("Dry-run only. No Procore API calls or file writes were made.")


if __name__ == "__main__":
    main()
