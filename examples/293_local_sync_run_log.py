"""Create a local sync run record and redacted JSONL log.

This example writes temporary local files only. It does not call Procore,
schedule jobs, or print secrets.
"""

from pathlib import Path
from tempfile import TemporaryDirectory

from pyprocore.integrations import (
    append_sync_log,
    complete_sync_run,
    create_sync_run,
    summarize_sync_runs,
)


def main() -> None:
    """Write and summarize a local sync run record."""
    with TemporaryDirectory() as temp_dir:
        output_dir = Path(temp_dir) / "sync-runs"
        run = create_sync_run("procore_to_jsonl_sync_worker", output_dir)
        append_sync_log(
            run,
            "Prepared local export plan",
            data={"record_count": 0, "access_token": "fake-token"},
        )
        complete_sync_run(run, summary={"records": 0})
        summary = summarize_sync_runs(output_dir)

        print(f"Local sync run written to: {output_dir}")
        print(f"Run count: {summary['run_count']}")
        print(f"Status counts: {summary['status_counts']}")
        print("Secret-like fields were redacted before writing logs.")


if __name__ == "__main__":
    main()
