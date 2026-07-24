"""Render local migration guides and their review artifacts."""

from __future__ import annotations

import json

from pyprocore.maintenance.models import (
    MigrationGuide,
    MigrationGuideArtifact,
    MigrationGuideReport,
)

_NOTICE = (
    "Local metadata only. No Procore call, remote fetch, code edit, patch application, "
    "git operation, GitHub API call, pull-request creation, MCP/tool execution, or "
    "external AI/model call is performed. Human review is required; this is not "
    "production compatibility certification."
)


def migration_guide_to_json(guide: MigrationGuide, *, pretty: bool = False) -> str:
    """Serialize a migration guide deterministically."""
    return json.dumps(
        guide.model_dump(mode="json"),
        indent=2 if pretty else None,
        sort_keys=True,
    )


def migration_guide_to_markdown(guide: MigrationGuide) -> str:
    """Render a complete human-readable migration guide."""
    lines = [
        f"# {guide.title}",
        "",
        _NOTICE,
        "",
        f"- From version: `{guide.from_version or 'not provided'}`",
        f"- To version: `{guide.to_version}`",
        f"- Contract comparison: {'yes' if guide.comparison_provided else 'no'}",
        f"- Overall risk: **{guide.overall_risk}**",
        "",
        "## Summary",
        "",
        guide.summary,
    ]
    for section in guide.sections:
        lines.extend(["", f"## {section.title}", "", section.summary, ""])
        lines.extend(
            [
                f"- **{item.risk_level} / {item.category}** `{item.subject}`: {item.summary}"
                for item in section.items
            ]
            or ["- None"]
        )
    lines.extend(
        [
            "",
            "## Recommended Upgrade Checklist",
            "",
            *_checklist(guide.recommended_upgrade_checklist),
            "",
            "## Manual Verification Checklist",
            "",
            *_checklist(guide.manual_verification_checklist),
            "",
            "## Suggested Test Plan",
            "",
            *_checklist(guide.suggested_test_plan),
            "",
            "## Notes for Maintainers",
            "",
            *[f"- {note}" for note in guide.maintainer_notes],
            "",
            "## Safety Notes",
            "",
            *[f"- {note}" for note in guide.safety_notes],
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def upgrade_checklist_to_markdown(guide: MigrationGuide) -> str:
    """Render only the human-owned upgrade checklist."""
    return _focused_report(
        "PyProcore Upgrade Checklist",
        guide,
        guide.recommended_upgrade_checklist,
    )


def migration_test_plan_to_markdown(guide: MigrationGuide) -> str:
    """Render a local-only test plan."""
    return _focused_report(
        "PyProcore Migration Test Plan",
        guide,
        guide.suggested_test_plan,
    )


def deprecation_summary_to_markdown(guide: MigrationGuide) -> str:
    """Render newly introduced deprecations."""
    lines = [
        "# PyProcore Deprecation Summary",
        "",
        _NOTICE,
        "",
        f"- From: `{guide.from_version or 'not provided'}`",
        f"- To: `{guide.to_version}`",
        "",
        "## Deprecations",
        "",
        *(
            [
                f"- **{row.risk_level}** `{row.helper}`: {row.migration_note}"
                for row in guide.deprecations
            ]
            or ["- None"]
        ),
    ]
    return "\n".join(lines).rstrip() + "\n"


def migration_guide_report_to_json(
    report: MigrationGuideReport,
    *,
    pretty: bool = False,
) -> str:
    """Serialize an artifact write or dry-run report."""
    return json.dumps(
        report.model_dump(mode="json"),
        indent=2 if pretty else None,
        sort_keys=True,
    )


def migration_guide_report_to_markdown(report: MigrationGuideReport) -> str:
    """Render an artifact write or dry-run report."""
    paths = report.planned_files if report.dry_run else report.written_files
    lines = [
        "# Migration Guide Artifact Report",
        "",
        _NOTICE,
        "",
        f"- Output directory: `{report.output_dir}`",
        f"- Dry-run: {'yes' if report.dry_run else 'no'}",
        f"- Customer files modified: {'yes' if report.customer_files_modified else 'no'}",
        f"- Patches applied: {'yes' if report.patches_applied else 'no'}",
        "",
        "## Files",
        "",
        *([f"- `{path}`" for path in paths] or ["- None"]),
    ]
    return "\n".join(lines).rstrip() + "\n"


def build_migration_guide_artifacts(
    guide: MigrationGuide,
) -> list[MigrationGuideArtifact]:
    """Build the fixed set of local migration-guide artifacts."""
    from pyprocore.maintenance.migration_guides import migration_guide_metadata

    return [
        MigrationGuideArtifact(
            relative_path="migration_guide.md",
            purpose="Complete human-readable migration guide.",
            content=migration_guide_to_markdown(guide),
        ),
        MigrationGuideArtifact(
            relative_path="migration_guide.json",
            purpose="Machine-readable migration guide.",
            content=migration_guide_to_json(guide, pretty=True) + "\n",
        ),
        MigrationGuideArtifact(
            relative_path="upgrade_checklist.md",
            purpose="Human-owned upgrade checklist.",
            content=upgrade_checklist_to_markdown(guide),
        ),
        MigrationGuideArtifact(
            relative_path="test_plan.md",
            purpose="Local, mocked migration test plan.",
            content=migration_test_plan_to_markdown(guide),
        ),
        MigrationGuideArtifact(
            relative_path="deprecation_summary.md",
            purpose="Focused deprecation summary.",
            content=deprecation_summary_to_markdown(guide),
        ),
        MigrationGuideArtifact(
            relative_path="metadata.json",
            purpose="Artifact safety and version metadata.",
            content=migration_guide_metadata(guide),
        ),
    ]


def _focused_report(title: str, guide: MigrationGuide, rows: list[str]) -> str:
    """Render one checklist-style report."""
    lines = [
        f"# {title}",
        "",
        _NOTICE,
        "",
        f"- From: `{guide.from_version or 'not provided'}`",
        f"- To: `{guide.to_version}`",
        "",
        *_checklist(rows),
    ]
    return "\n".join(lines).rstrip() + "\n"


def _checklist(rows: list[str]) -> list[str]:
    """Render checklist rows."""
    return [f"- [ ] {row}" for row in rows] or ["- None"]
