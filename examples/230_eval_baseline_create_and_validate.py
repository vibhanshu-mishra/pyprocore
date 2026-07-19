"""Write and validate a local eval baseline in a temporary folder.

The temporary file is safe to delete. No live Procore or AI/model calls are made.
"""

from pathlib import Path
from tempfile import TemporaryDirectory

from pyprocore.evals import (
    baseline_to_summary,
    build_eval_baseline,
    load_eval_baseline_from_file,
    run_builtin_eval_suites,
    write_eval_baseline_json,
)


def main() -> None:
    """Create, write, reload, and summarize a baseline."""
    with TemporaryDirectory() as temp_dir:
        output_path = Path(temp_dir) / "eval_baseline.json"
        report = run_builtin_eval_suites(suite="submittal_workflow_golden")
        baseline = build_eval_baseline(report, baseline_name="local-submittal-baseline")
        write_eval_baseline_json(baseline, output_path)
        reloaded = load_eval_baseline_from_file(output_path)
        print(f"Baseline written to: {output_path}")
        print(baseline_to_summary(reloaded))


if __name__ == "__main__":
    main()
