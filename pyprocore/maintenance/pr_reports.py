"""JSON and Markdown reports for local pull-request draft packs."""

from __future__ import annotations

import json

from pyprocore.maintenance.models import (
    PullRequestDraftArtifact,
    PullRequestDraftPack,
    PullRequestDraftReport,
    PullRequestDraftRiskSummary,
)
from pyprocore.maintenance.patch_reports import migration_patch_plan_to_markdown

_SAFETY_NOTE = (
    "Local PR-draft artifacts only. No customer files were modified, no patches "
    "were applied, no git operations or GitHub API calls were made, no pull "
    "request was opened, no remote repository or OAS file was fetched, and no "
    "Procore, MCP/tool, or external AI/model call was made. Human review is required."
)


def pr_draft_pack_to_json(
    pack: PullRequestDraftPack,
    *,
    pretty: bool = False,
) -> str:
    """Serialize a local PR draft pack to JSON."""
    return json.dumps(
        pack.model_dump(mode="json"),
        indent=2 if pretty else None,
        sort_keys=pretty,
    )


def pr_draft_pack_to_markdown(pack: PullRequestDraftPack) -> str:
    """Render a local PR draft pack report as Markdown."""
    lines = [
        "# Local Pull Request Draft Pack",
        "",
        _SAFETY_NOTE,
        "",
        "## Draft Title",
        "",
        pack.title,
        "",
        "## Draft Body Preview",
        "",
        pack.body,
        "",
        "## Artifact List",
        "",
        *[f"- `{artifact.relative_path}`: {artifact.purpose}" for artifact in pack.artifacts],
    ]
    return "\n".join(lines).rstrip() + "\n"


def pr_draft_report_to_json(
    report: PullRequestDraftReport,
    *,
    pretty: bool = False,
) -> str:
    """Serialize a PR draft artifact dry-run or write report to JSON."""
    return json.dumps(
        report.model_dump(mode="json"),
        indent=2 if pretty else None,
        sort_keys=pretty,
    )


def pr_draft_report_to_markdown(report: PullRequestDraftReport) -> str:
    """Render a PR draft artifact dry-run or write report as Markdown."""
    paths = report.planned_files if report.dry_run else report.written_files
    lines = [
        "# Local PR Draft Artifact Report",
        "",
        _SAFETY_NOTE,
        "",
        f"- Scanned path: `{report.pack.scanned_path}`",
        f"- Output directory: `{report.output_dir}`",
        f"- Dry-run: {'yes' if report.dry_run else 'no'}",
        f"- Artifacts: {len(report.artifacts)}",
        "",
        "## Artifact Paths",
        "",
        *([f"- `{path}`" for path in paths] or ["- None"]),
    ]
    return "\n".join(lines).rstrip() + "\n"


def pr_review_checklist_to_markdown(pack: PullRequestDraftPack) -> str:
    """Render a PR draft human-review checklist as Markdown."""
    lines = ["# Pull Request Review Checklist", "", _SAFETY_NOTE, ""]
    lines.extend(
        f"- [{'x' if item.completed else ' '}] {item.text}" for item in pack.review_checklist
    )
    return "\n".join(lines).rstrip() + "\n"


def pr_test_plan_to_markdown(pack: PullRequestDraftPack) -> str:
    """Render a safe manual test plan without live Procore commands."""
    lines = ["# Pull Request Test Plan", "", _SAFETY_NOTE, ""]
    lines.extend(f"{index}. {step}" for index, step in enumerate(pack.test_plan, 1))
    return "\n".join(lines).rstrip() + "\n"


def pr_risk_summary_to_markdown(summary: PullRequestDraftRiskSummary) -> str:
    """Render grouped migration review risks as Markdown."""
    lines = ["# Pull Request Risk Summary", "", _SAFETY_NOTE]
    for heading, rows in [
        ("High", summary.high),
        ("Medium", summary.medium),
        ("Low", summary.low),
        ("Unknown / Manual Review", summary.unknown_manual_review),
    ]:
        lines.extend(["", f"## {heading}", ""])
        lines.extend(
            [
                f"- `{row.file_path}:{row.line_number or '?'}` "
                f"**{row.category}**: {row.message}"
                for row in rows
            ]
            or ["- None"]
        )
    return "\n".join(lines).rstrip() + "\n"


def build_pr_draft_artifacts(
    pack: PullRequestDraftPack,
) -> list[PullRequestDraftArtifact]:
    """Build the fixed local-only PR draft artifact set."""
    diffs = "\n\n".join(
        hunk.unified_diff for file in pack.migration_plan.files for hunk in file.hunks
    )
    metadata = pack.model_dump(mode="json", exclude={"artifacts"})
    return [
        PullRequestDraftArtifact(
            relative_path="title.txt",
            purpose="Conservative draft pull-request title",
            content=pack.title.rstrip() + "\n",
        ),
        PullRequestDraftArtifact(
            relative_path="body.md",
            purpose="Human-review pull-request body draft",
            content=pack.body.rstrip() + "\n",
        ),
        PullRequestDraftArtifact(
            relative_path="review_checklist.md",
            purpose="Human-review checklist",
            content=pr_review_checklist_to_markdown(pack),
        ),
        PullRequestDraftArtifact(
            relative_path="test_plan.md",
            purpose="Safe manual test plan",
            content=pr_test_plan_to_markdown(pack),
        ),
        PullRequestDraftArtifact(
            relative_path="risk_summary.md",
            purpose="Grouped migration risk summary",
            content=pr_risk_summary_to_markdown(pack.risk_summary),
        ),
        PullRequestDraftArtifact(
            relative_path="impacted_files.json",
            purpose="Detected files requiring review",
            content=json.dumps(pack.impacted_files, indent=2) + "\n",
        ),
        PullRequestDraftArtifact(
            relative_path="suggested_changes.diff",
            purpose="Non-applied safe documentation diff suggestions",
            content=(diffs or "# No safe diff suggestions.") + "\n",
        ),
        PullRequestDraftArtifact(
            relative_path="migration_report.md",
            purpose="Underlying local migration report",
            content=migration_patch_plan_to_markdown(pack.migration_plan),
        ),
        PullRequestDraftArtifact(
            relative_path="metadata.json",
            purpose="Machine-readable PR draft metadata",
            content=json.dumps(metadata, indent=2, sort_keys=True) + "\n",
        ),
    ]
