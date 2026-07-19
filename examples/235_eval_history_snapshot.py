"""Append a local eval history snapshot in a temporary folder."""

from pathlib import Path
from tempfile import TemporaryDirectory

from pyprocore.evals import (
    append_eval_history_snapshot,
    build_eval_history_snapshot,
    run_builtin_eval_suites,
)


def main() -> None:
    """Create and append one local history snapshot."""
    with TemporaryDirectory() as temp_dir:
        history_path = Path(temp_dir) / "eval_history.json"
        report = run_builtin_eval_suites(suite="rfi_workflow_golden")
        snapshot = build_eval_history_snapshot(report, label="local-rfi-check")
        append_eval_history_snapshot(history_path, snapshot)
        print(f"History snapshot written to: {history_path}")
        print(f"Snapshot score: {snapshot.score}/{snapshot.max_score}")


if __name__ == "__main__":
    main()
