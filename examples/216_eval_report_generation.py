"""Write local eval reports to a temporary directory.

This demonstrates JSON and Markdown report generation without committing
generated reports or calling Procore.
"""

from pathlib import Path
from tempfile import TemporaryDirectory

from pyprocore.evals import (
    run_builtin_eval_suites,
    write_eval_report_json,
    write_eval_report_markdown,
)


def main() -> None:
    """Create temporary local eval report files."""
    report = run_builtin_eval_suites(suite="golden_export_rows_basic")
    with TemporaryDirectory() as temp_dir:
        output_dir = Path(temp_dir)
        json_path = write_eval_report_json(report, output_dir / "eval-report.json")
        markdown_path = write_eval_report_markdown(report, output_dir / "eval-report.md")
        print(f"Wrote JSON report: {json_path}")
        print(f"Wrote Markdown report: {markdown_path}")


if __name__ == "__main__":
    main()
