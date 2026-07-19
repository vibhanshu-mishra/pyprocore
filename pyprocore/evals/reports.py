"""Report builders for local deterministic PyProcore evals."""

from __future__ import annotations

import json
from pathlib import Path

from pyprocore.core.exceptions import ValidationError
from pyprocore.evals.models import EvalReport


def eval_report_to_json(report: EvalReport, *, pretty: bool = True) -> str:
    """Serialize an eval report to deterministic JSON text.

    Args:
        report: Eval report to serialize.
        pretty: Whether to format with indentation.

    Returns:
        JSON report string.
    """
    return json.dumps(
        report.model_dump(mode="json"),
        indent=2 if pretty else None,
        sort_keys=True,
    )


def eval_report_to_markdown(report: EvalReport) -> str:
    """Render an eval report as beginner-friendly Markdown."""
    lines = [
        "# PyProcore Golden Eval Report",
        "",
        f"Status: `{report.status.value}`",
        f"Mode: `{report.mode}`",
        f"PyProcore version: `{report.pyprocore_version}`",
        f"Suites passed: {report.passed_suites}/{report.total_suites}",
        f"Cases passed: {report.passed_cases}/{report.total_cases}",
        f"Score: {report.score}/{report.max_score}",
        "",
        "| Suite | Status | Cases | Score | Warnings |",
        "| --- | --- | ---: | ---: | ---: |",
    ]
    for suite in report.suites:
        lines.append(
            f"| `{suite.suite_name}` | `{suite.status.value}` | "
            f"{suite.passed_cases}/{suite.total_cases} | "
            f"{suite.score}/{suite.max_score} | {suite.warnings} |"
        )
    lines.extend(
        [
            "",
            "Mode: local deterministic fixtures only; no Procore, model, plugin, "
            "MCP, or tool execution occurred.",
            "",
        ]
    )
    return "\n".join(lines)


def write_eval_report_json(
    report: EvalReport,
    output_path: Path | str,
    *,
    pretty: bool = True,
) -> Path:
    """Write an eval report JSON file to a safe local path."""
    path = _validate_local_output_path(output_path, allowed_suffix=".json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(eval_report_to_json(report, pretty=pretty) + "\n", encoding="utf-8")
    return path


def write_eval_report_markdown(report: EvalReport, output_path: Path | str) -> Path:
    """Write an eval report Markdown file to a safe local path."""
    path = _validate_local_output_path(output_path, allowed_suffix=".md")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(eval_report_to_markdown(report), encoding="utf-8")
    return path


def _validate_local_output_path(path: Path | str, *, allowed_suffix: str) -> Path:
    """Validate a local report output path."""
    output_path = Path(path)
    path_text = str(output_path)
    if "://" in path_text or path_text.casefold().startswith(("http:", "https:")):
        raise ValidationError("Eval report output path must be local, not a URL.")
    if any(part == ".." for part in output_path.parts):
        raise ValidationError("Eval report output path must not contain path traversal.")
    if output_path.suffix != allowed_suffix:
        raise ValidationError(f"Eval report output path must end with {allowed_suffix}.")
    return output_path
