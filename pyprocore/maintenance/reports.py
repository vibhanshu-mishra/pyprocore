"""JSON and Markdown rendering for API maintenance assistant reports."""

from __future__ import annotations

import json

from pyprocore.maintenance.models import (
    ApiCompatibilityContract,
    ApiCompatibilityDiffReport,
    ApiCompatibilityValidationReport,
    ApiCoverageGap,
    ApiCoverageGapReport,
    ApiDriftReport,
    ApiImpactReport,
    ApiMaintenancePlan,
    ApiMaintenanceTask,
    ApiScaffoldCopyResult,
    ApiScaffoldPlan,
    CodebaseCompatibilityReport,
    CodebaseScanReport,
    MigrationGuide,
    MigrationGuideReport,
    MigrationPatchPlan,
    MigrationPatchReport,
    PullRequestDraftPack,
    PullRequestDraftReport,
)


def maintenance_report_to_json(
    report: (
        ApiDriftReport
        | ApiCompatibilityContract
        | ApiCompatibilityDiffReport
        | ApiCompatibilityValidationReport
        | ApiCoverageGapReport
        | ApiMaintenancePlan
        | ApiScaffoldPlan
        | ApiScaffoldCopyResult
        | CodebaseScanReport
        | CodebaseCompatibilityReport
        | ApiImpactReport
        | MigrationPatchPlan
        | MigrationPatchReport
        | MigrationGuide
        | MigrationGuideReport
        | PullRequestDraftPack
        | PullRequestDraftReport
    ),
    *,
    pretty: bool = False,
) -> str:
    """Serialize a maintenance assistant report to JSON."""
    return json.dumps(
        report.model_dump(mode="json"),
        indent=2 if pretty else None,
        sort_keys=pretty,
    )


def drift_report_to_markdown(report: ApiDriftReport) -> str:
    """Render an API drift report as Markdown."""
    lines = _header(
        "API Drift Report",
        [
            f"Old source: `{report.old_source_path}`",
            f"New source: `{report.new_source_path}`",
            f"Added endpoint operations: {len(report.added_endpoints)}",
            f"Removed endpoint operations: {len(report.removed_endpoints)}",
            f"Changed method sets: {len(report.changed_methods)}",
            f"Changed parameters: {len(report.changed_parameters)}",
            f"Changed operation IDs: {len(report.changed_operation_ids)}",
            f"Risky changes: {len(report.risky_changes)}",
        ],
    )
    for title, changes in [
        ("Added Endpoints", report.added_endpoints),
        ("Removed Endpoints", report.removed_endpoints),
        ("Changed Methods", report.changed_methods),
        ("Changed Parameters", report.changed_parameters),
        ("Changed Operation IDs", report.changed_operation_ids),
        ("Risky Changes", report.risky_changes),
    ]:
        lines.extend(["", f"## {title}", ""])
        lines.extend(
            [
                f"- `{change.method or '*'} {change.path}` - {change.change_type}"
                for change in changes
            ]
            or ["- None"]
        )
    return _finish(lines)


def coverage_gap_report_to_markdown(report: ApiCoverageGapReport) -> str:
    """Render an API coverage-gap report as Markdown."""
    lines = _header(
        "API Coverage Gap Report",
        [
            f"Source: `{report.source_path}`",
            f"Supported areas found: {len(report.supported_areas)}",
            f"Unsupported read-only candidates: {len(report.unsupported_read_only)}",
            f"Risky/write deferred: {len(report.unsupported_risky_write)}",
            f"Unknown/deferred: {len(report.unknown)}",
        ],
    )
    lines.extend(["", "## Recommended Read-only Candidates", ""])
    lines.extend(_gap_bullets(report.recommended_next_candidates))
    lines.extend(["", "## Deferred Candidates", ""])
    lines.extend(_gap_bullets(report.deferred_candidates))
    return _finish(lines)


def maintenance_plan_to_markdown(report: ApiMaintenancePlan) -> str:
    """Render an API maintenance plan as Markdown."""
    lines = _header(
        "API Maintenance Plan",
        [
            f"Source: `{report.source_path}`",
            f"Safe read-only candidates: {len(report.safe_read_only_candidates)}",
            f"Needs endpoint-shape review: {len(report.needs_endpoint_shape_review)}",
            f"Risky/write deferred: {len(report.risky_write_deferred)}",
            f"Docs-only updates: {len(report.docs_only_updates)}",
        ],
    )
    for title, tasks in [
        ("Safe Read-only Candidates", report.safe_read_only_candidates),
        ("Needs Endpoint-shape Review", report.needs_endpoint_shape_review),
        ("Risky/write Deferred", report.risky_write_deferred),
        ("Docs-only Updates", report.docs_only_updates),
        ("Tests and Examples Needed", report.tests_examples_needed),
    ]:
        lines.extend(["", f"## {title}", ""])
        lines.extend(_task_bullets(tasks))
    return _finish(lines)


def scaffold_plan_to_markdown(report: ApiScaffoldPlan) -> str:
    """Render a draft scaffold plan as Markdown."""
    lines = _header(
        "Read-only Endpoint Scaffold Plan",
        [
            f"Source: `{report.source_path}`",
            f"Endpoint: `{report.method} {report.endpoint_path}`",
            f"Safety: {report.safety_classification.value}",
            f"Allowed: {'yes' if report.allowed else 'no'}",
            f"Draft files: {len(report.files)}",
        ],
    )
    lines.extend(["", "## Draft Files", ""])
    lines.extend(
        [f"- `{item.relative_path}` - {item.purpose}" for item in report.files] or ["- None"]
    )
    return _finish(lines)


def scaffold_copy_result_to_markdown(report: ApiScaffoldCopyResult) -> str:
    """Render a scaffold dry-run or local copy result as Markdown."""
    lines = _header(
        "Read-only Endpoint Scaffold Result",
        [
            f"Output directory: `{report.output_dir}`",
            f"Dry-run: {'yes' if report.dry_run else 'no'}",
            f"Files written: {len(report.written_files)}",
            f"Files planned without writing: {len(report.skipped_files)}",
        ],
    )
    lines.extend(["", "## Paths", ""])
    lines.extend(
        [f"- `{path}`" for path in [*report.written_files, *report.skipped_files]] or ["- None"]
    )
    return _finish(lines)


def _header(title: str, summary: list[str]) -> list[str]:
    """Build a report heading and safety statement."""
    return [
        f"# {title}",
        "",
        "Local OAS files only. No remote fetch, live Procore calls, executable tool "
        "generation, SDK auto-update, commits, pull requests, publishing, or write "
        "actions are enabled. Human review is required.",
        "",
        "## Summary",
        "",
        *[f"- {item}" for item in summary],
    ]


def _gap_bullets(gaps: list[ApiCoverageGap]) -> list[str]:
    """Render coverage gaps as Markdown bullets."""
    return [
        f"- `{gap.endpoint.method} {gap.endpoint.path}` ({gap.resource_family}) - "
        f"{gap.recommendation}"
        for gap in gaps
    ] or ["- None"]


def _task_bullets(tasks: list[ApiMaintenanceTask]) -> list[str]:
    """Render maintenance tasks as Markdown bullets."""
    return [
        f"- `{task.method} {task.endpoint_path}` ({task.resource_family}) - "
        f"{task.safety_classification.value}"
        for task in tasks
    ] or ["- None"]


def _finish(lines: list[str]) -> str:
    """Add a final review reminder and normalize trailing newline."""
    lines.extend(["", "Human review is required before any SDK implementation."])
    return "\n".join(lines).rstrip() + "\n"
