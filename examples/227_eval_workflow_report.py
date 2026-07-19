"""Generate a local Markdown report for workflow-specific evals.

The report is written to a temporary directory so this example does not leave
release artifacts in the repository.
"""

from pathlib import Path
from tempfile import TemporaryDirectory

from pyprocore.evals import run_builtin_eval_suites, write_eval_report_markdown


def main() -> None:
    """Write a temporary Markdown report for one workflow suite."""
    report = run_builtin_eval_suites(suite="safety_boundaries_golden")
    with TemporaryDirectory() as temp_dir:
        output_path = write_eval_report_markdown(report, Path(temp_dir) / "workflow-evals.md")
        print(f"Wrote local workflow eval report: {output_path}")


if __name__ == "__main__":
    main()
