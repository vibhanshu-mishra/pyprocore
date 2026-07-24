"""JSON, Markdown, checklist, and artifact reports for migration plans."""

from __future__ import annotations

import json

from pyprocore.maintenance.models import (
    MigrationPatchArtifact,
    MigrationPatchPlan,
    MigrationPatchReport,
)

_SAFETY_NOTE = (
    "Local scan and review artifacts only. No customer files are modified, no "
    "patches are applied, no remote repository or OAS file is fetched, no Procore "
    "or external AI/model call is made, and no MCP, tool, git, commit, pull-request, "
    "or write execution is enabled. Human review is required."
)


def migration_patch_plan_to_json(
    plan: MigrationPatchPlan,
    *,
    pretty: bool = False,
) -> str:
    """Serialize a migration patch plan to JSON."""
    return json.dumps(
        plan.model_dump(mode="json"),
        indent=2 if pretty else None,
        sort_keys=pretty,
    )


def migration_patch_plan_to_markdown(plan: MigrationPatchPlan) -> str:
    """Render a migration patch plan as Markdown."""
    lines = [
        "# PyProcore Migration Patch Plan",
        "",
        _SAFETY_NOTE,
        "",
        "## Summary",
        "",
        f"- Scanned path: `{plan.scanned_path}`",
        f"- OAS comparison provided: "
        f"{'yes' if plan.impact_report.oas_comparison_provided else 'no'}",
        f"- Detected usage rows: {len(plan.impact_report.scan_report.usages)}",
        f"- Impacted files: {len(plan.impacted_files)}",
        f"- Patch suggestions: {len(plan.suggestions)}",
        f"- Suggested diff hunks: {sum(len(item.hunks) for item in plan.files)}",
        "",
        "## Impacted Files",
        "",
        *([f"- `{path}`" for path in plan.impacted_files] or ["- None"]),
    ]
    for severity in ["high", "medium", "unknown", "low"]:
        rows = [suggestion for suggestion in plan.suggestions if suggestion.severity == severity]
        lines.extend(["", f"## {severity.title()} Priority Suggestions", ""])
        lines.extend(
            [
                f"- `{row.file_path}:{row.line_number or '?'}` "
                f"**{row.category}**: {row.message}"
                for row in rows
            ]
            or ["- None"]
        )
    lines.extend(["", "## Suggested Diffs", ""])
    hunks = [hunk for file in plan.files for hunk in file.hunks]
    if hunks:
        for hunk in hunks:
            lines.extend(["", "```diff", hunk.unified_diff, "```"])
    else:
        lines.append("- None; ambiguous or code usage remains manual-review only.")
    lines.extend(["", "## Manual Review Checklist", ""])
    lines.extend([f"{index}. {item}" for index, item in enumerate(plan.manual_review_checklist, 1)])
    return "\n".join(lines).rstrip() + "\n"


def manual_review_checklist_to_markdown(plan: MigrationPatchPlan) -> str:
    """Render only the manual review checklist as Markdown."""
    lines = [
        "# Migration Manual Review Checklist",
        "",
        _SAFETY_NOTE,
        "",
        *[f"{index}. {item}" for index, item in enumerate(plan.manual_review_checklist, start=1)],
    ]
    return "\n".join(lines).rstrip() + "\n"


def migration_patch_report_to_json(
    report: MigrationPatchReport,
    *,
    pretty: bool = False,
) -> str:
    """Serialize an artifact dry-run or write report to JSON."""
    return json.dumps(
        report.model_dump(mode="json"),
        indent=2 if pretty else None,
        sort_keys=pretty,
    )


def migration_patch_report_to_markdown(report: MigrationPatchReport) -> str:
    """Render an artifact dry-run or write report as Markdown."""
    paths = report.planned_files if report.dry_run else report.written_files
    lines = [
        "# Migration Patch Artifact Report",
        "",
        _SAFETY_NOTE,
        "",
        f"- Output directory: `{report.output_dir}`",
        f"- Dry-run: {'yes' if report.dry_run else 'no'}",
        f"- Artifacts: {len(report.artifacts)}",
        "",
        "## Artifact Paths",
        "",
        *([f"- `{path}`" for path in paths] or ["- None"]),
    ]
    return "\n".join(lines).rstrip() + "\n"


def build_migration_patch_artifacts(
    plan: MigrationPatchPlan,
) -> list[MigrationPatchArtifact]:
    """Build the fixed set of optional local migration review artifacts."""
    suggested_diffs = "\n\n".join(hunk.unified_diff for file in plan.files for hunk in file.hunks)
    impacted_files = json.dumps(plan.impacted_files, indent=2)
    return [
        MigrationPatchArtifact(
            relative_path="migration_report.md",
            purpose="Human-readable migration patch plan",
            content=migration_patch_plan_to_markdown(plan),
        ),
        MigrationPatchArtifact(
            relative_path="migration_report.json",
            purpose="Machine-readable migration patch plan",
            content=migration_patch_plan_to_json(plan, pretty=True) + "\n",
        ),
        MigrationPatchArtifact(
            relative_path="suggested_changes.diff",
            purpose="Non-applied safe documentation diff suggestions",
            content=(suggested_diffs or "# No safe diff suggestions.\n") + "\n",
        ),
        MigrationPatchArtifact(
            relative_path="impacted_files.json",
            purpose="Customer files requiring human review",
            content=impacted_files + "\n",
        ),
        MigrationPatchArtifact(
            relative_path="manual_review_checklist.md",
            purpose="Manual migration review checklist",
            content=manual_review_checklist_to_markdown(plan),
        ),
    ]
