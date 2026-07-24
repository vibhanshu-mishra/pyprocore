"""Report renderers for local project health analytics recipes."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from pyprocore.analytics.models import (
    ChangeExposureSummary,
    DailyLogCompletenessSummary,
    ProjectHealthFinding,
    ProjectHealthRecipeResult,
    ProjectHealthReport,
    RfiAgingSummary,
    SubmittalDelaySummary,
)


def analytics_result_to_json(
    result: ProjectHealthRecipeResult,
    *,
    pretty: bool = False,
) -> str:
    """Serialize an analytics recipe result to JSON."""
    return json.dumps(
        result.model_dump(mode="json"),
        indent=2 if pretty else None,
        sort_keys=pretty,
    )


def analytics_result_to_markdown(result: ProjectHealthRecipeResult) -> str:
    """Render an analytics recipe result as Markdown."""
    summary = result.summary
    lines = _report_header(result.recipe)
    if isinstance(summary, RfiAgingSummary):
        lines.extend(
            [
                f"- Records: {summary.record_count}",
                f"- Open RFIs: {summary.open_count}",
                f"- Overdue RFIs: {summary.overdue_count}",
                f"- Average age days: {summary.average_age_days}",
                f"- Max age days: {summary.max_age_days}",
                f"- Risk score: {summary.risk_score}",
                f"- Severity: {summary.severity}",
            ]
        )
    elif isinstance(summary, SubmittalDelaySummary):
        lines.extend(
            [
                f"- Records: {summary.record_count}",
                f"- Pending submittals: {summary.pending_count}",
                f"- Overdue submittals: {summary.overdue_count}",
                f"- Due soon: {summary.due_soon_count}",
                f"- Average days overdue: {summary.average_days_overdue}",
                f"- Risk score: {summary.risk_score}",
                f"- Severity: {summary.severity}",
            ]
        )
    elif isinstance(summary, ChangeExposureSummary):
        lines.extend(
            [
                f"- Records: {summary.record_count}",
                f"- Total estimated exposure: {summary.total_estimated_exposure}",
                f"- Open exposure: {summary.open_exposure}",
                f"- Approved exposure: {summary.approved_exposure}",
                f"- Rejected or void exposure: {summary.rejected_or_void_exposure}",
                f"- Risk score: {summary.risk_score}",
                f"- Severity: {summary.severity}",
            ]
        )
    elif isinstance(summary, DailyLogCompletenessSummary):
        lines.extend(
            [
                f"- Records: {summary.record_count}",
                f"- Expected dates: {summary.expected_date_count}",
                f"- Days with logs: {summary.days_with_logs}",
                f"- Missing days: {len(summary.missing_days)}",
                f"- Completeness percentage: {summary.completeness_percentage}",
                f"- Risk score: {summary.risk_score}",
                f"- Severity: {summary.severity}",
            ]
        )
    elif isinstance(summary, ProjectHealthReport):
        lines.extend(_project_health_lines(summary))
    lines.extend(_finding_lines(_findings(summary)))
    return "\n".join(lines).rstrip() + "\n"


def analytics_result_to_summary_dict(result: ProjectHealthRecipeResult) -> dict[str, Any]:
    """Return a compact dictionary summary for one analytics recipe result."""
    summary = result.summary
    payload = summary.model_dump(mode="json")
    compact: dict[str, Any] = {
        "recipe": result.recipe,
        "data_source": result.data_source,
        "procore_api_call_required": False,
        "external_ai_call_required": False,
        "write_actions_enabled": False,
    }
    for key in (
        "risk_score",
        "severity",
        "overall_score",
        "health_label",
        "record_count",
        "open_count",
        "pending_count",
        "overdue_count",
        "open_exposure",
        "completeness_percentage",
    ):
        if key in payload:
            compact[key] = payload[key]
    return compact


def write_analytics_summary_csv(
    results: list[ProjectHealthRecipeResult],
    path: Path | str,
) -> Path:
    """Write compact analytics result summaries to a local CSV file."""
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    rows = [analytics_result_to_summary_dict(result) for result in results]
    fieldnames = sorted({key for row in rows for key in row})
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return output_path


def _report_header(recipe: str) -> list[str]:
    title = recipe.replace("_", " ").title()
    return [
        f"# {title} Analytics Report",
        "",
        "- Data source: local/exported records only",
        "- Procore API calls made: false",
        "- External AI/model calls made: false",
        "- Procore write actions performed: false",
        "- Scoring: heuristic and review-oriented, not a guarantee",
        "",
    ]


def _project_health_lines(report: ProjectHealthReport) -> list[str]:
    lines = [
        f"- Overall score: {report.overall_score}",
        f"- Health label: {report.health_label}",
        "",
        "## Component Scores",
        "",
        "| Component | Score | Normalized Weight |",
        "| --- | ---: | ---: |",
    ]
    for name, score in report.component_scores.items():
        lines.append(f"| {name} | {score} | {report.component_weights.get(name, 0)} |")
    lines.extend(["", "## Recommended Next Reviews", ""])
    for recommendation in report.recommended_next_reviews:
        lines.append(f"- {recommendation}")
    return lines


def _findings(summary: object) -> list[ProjectHealthFinding]:
    if isinstance(summary, ProjectHealthReport):
        return summary.top_findings
    if isinstance(
        summary,
        (
            RfiAgingSummary,
            SubmittalDelaySummary,
            ChangeExposureSummary,
            DailyLogCompletenessSummary,
        ),
    ):
        return summary.findings
    return []


def _finding_lines(findings: list[ProjectHealthFinding]) -> list[str]:
    lines = ["", "## Review Findings", ""]
    if not findings:
        return lines + ["- No review findings generated from the local input records."]
    for finding in findings:
        lines.append(f"- **{finding.severity}** {finding.title}: {finding.reason}")
    return lines
