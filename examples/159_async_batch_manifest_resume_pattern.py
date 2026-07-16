"""Show the async batch manifest resume/skip pattern locally."""

from __future__ import annotations

from pyprocore import (
    AsyncBatchResourceResult,
    build_async_batch_dry_run_manifest,
    build_async_batch_plan,
)


def main() -> None:
    """Create a manifest and mark one pair as completed for resume planning."""
    plan = build_async_batch_plan(
        company_id=12345,
        project_ids=[67890],
        resources=["rfis", "submittals"],
        dry_run=True,
    )
    manifest = build_async_batch_dry_run_manifest(plan)
    completed = AsyncBatchResourceResult(
        project_id=67890,
        resource="rfis",
        status="completed",
        record_count=12,
    )
    manifest.results[0] = completed
    print("Completed pairs in manifest can be skipped by live library batch runs.")
    print(f"Completed: {manifest.completed_count}")


if __name__ == "__main__":
    main()
