"""Build and optionally write local-only pull-request draft packs."""

from __future__ import annotations

from pathlib import Path

from pyprocore.core.exceptions import ValidationError
from pyprocore.maintenance.migration import build_migration_patch_plan
from pyprocore.maintenance.models import (
    MigrationPatchPlan,
    MigrationPatchPlanOptions,
    MigrationPatchSuggestion,
    MigrationSafetyFinding,
    PullRequestDraftArtifact,
    PullRequestDraftChecklistItem,
    PullRequestDraftOptions,
    PullRequestDraftPack,
    PullRequestDraftReport,
    PullRequestDraftRiskSummary,
    PullRequestDraftSection,
)
from pyprocore.maintenance.patch_plan import _validate_artifact_path
from pyprocore.maintenance.pr_reports import build_pr_draft_artifacts

_SAFETY_TEXT = (
    "No customer files were modified. No patches were applied. No GitHub PR was "
    "opened. No git commands were run. No GitHub API, Procore API, remote repository, "
    "remote OAS, MCP/tool, or external AI/model call was used. Human review is required."
)


def build_pr_draft_pack(
    codebase_path: str | Path,
    old_oas_path: str | Path | None = None,
    new_oas_path: str | Path | None = None,
    options: PullRequestDraftOptions | None = None,
) -> PullRequestDraftPack:
    """Build a local PR draft pack from usage and optional OAS drift metadata.

    Args:
        codebase_path: User-selected local customer codebase.
        old_oas_path: Optional earlier local OAS JSON file.
        new_oas_path: Optional newer local OAS JSON file.
        options: Optional draft content settings.

    Returns:
        Typed PR draft pack requiring human review.
    """
    draft_options = options or PullRequestDraftOptions()
    migration_plan = build_migration_patch_plan(
        codebase_path,
        old_oas_path=old_oas_path,
        new_oas_path=new_oas_path,
        options=MigrationPatchPlanOptions(
            include_suggested_diffs=draft_options.include_suggested_changes,
            include_no_action_suggestions=draft_options.include_no_action_suggestions,
        ),
    )
    title = _default_title(migration_plan.impact_report.oas_comparison_provided)
    checklist = _build_review_checklist(migration_plan.suggestions)
    test_plan = _build_test_plan()
    risk_summary = _build_risk_summary(migration_plan.suggestions)
    sections = _build_body_sections(migration_plan, checklist, test_plan)
    body = "\n\n".join(f"## {section.heading}\n\n{section.content}" for section in sections)
    pack = PullRequestDraftPack(
        scanned_path=migration_plan.scanned_path,
        options=draft_options,
        migration_plan=migration_plan,
        title=title,
        body=body,
        sections=sections,
        review_checklist=checklist,
        test_plan=test_plan,
        risk_summary=risk_summary,
        impacted_files=migration_plan.impacted_files,
    )
    return pack.model_copy(update={"artifacts": build_pr_draft_artifacts(pack)})


def write_pr_draft_pack(
    pack: PullRequestDraftPack,
    output_dir: str | Path,
    *,
    dry_run: bool = True,
    overwrite: bool = False,
) -> PullRequestDraftReport:
    """Plan or write PR draft artifacts beneath one explicit output directory.

    Args:
        pack: Typed local PR draft pack.
        output_dir: Directory reserved for generated draft artifacts.
        dry_run: Validate and list artifacts without writing.
        overwrite: Permit replacing existing draft artifact files.

    Returns:
        Typed dry-run or local artifact-write report.

    Raises:
        ValidationError: If a path escapes the output directory or overwrite
            permission is required.
    """
    root = Path(output_dir).expanduser().resolve()
    destinations: list[tuple[PullRequestDraftArtifact, Path]] = []
    for artifact in pack.artifacts:
        relative_path = _validate_artifact_path(artifact.relative_path)
        destination = (root / relative_path).resolve()
        if not destination.is_relative_to(root):
            raise ValidationError(
                f"PR draft artifact path must remain inside output directory: {relative_path}"
            )
        if destination.exists() and not overwrite:
            raise ValidationError(
                "PR draft artifact already exists; use --overwrite explicitly: " f"{destination}"
            )
        destinations.append((artifact, destination))

    if dry_run:
        return PullRequestDraftReport(
            pack=pack,
            output_dir=str(root),
            dry_run=True,
            artifacts=pack.artifacts,
            planned_files=[str(destination) for _, destination in destinations],
            findings=[
                MigrationSafetyFinding(
                    severity="info",
                    code="dry_run",
                    message="Dry-run completed; no PR draft artifacts were written.",
                )
            ],
        )

    written: list[str] = []
    for artifact, destination in destinations:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(artifact.content, encoding="utf-8")
        written.append(str(destination))
    return PullRequestDraftReport(
        pack=pack,
        output_dir=str(root),
        dry_run=False,
        artifacts=pack.artifacts,
        written_files=written,
        findings=[
            MigrationSafetyFinding(
                severity="warning",
                code="draft_artifacts_written",
                message=(
                    "PR draft artifacts were written only to the selected output "
                    "directory. No customer files were modified and no PR was opened."
                ),
            )
        ],
    )


def _default_title(oas_comparison_provided: bool) -> str:
    """Return a conservative title that never claims fixes were applied."""
    if oas_comparison_provided:
        return "Review PyProcore migration impact from API drift"
    return "Review local PyProcore usage after API changes"


def _build_review_checklist(
    suggestions: list[MigrationPatchSuggestion],
) -> list[PullRequestDraftChecklistItem]:
    """Build a stable checklist plus context-sensitive review items."""
    items = [
        ("scope", "Confirm impacted files are correct."),
        ("tests", "Run the customer project's unit tests manually."),
        ("security", "Review secret redaction and confirm no secrets are committed."),
        ("safety", "Verify no Procore write endpoints are introduced."),
        (
            "patches",
            "Apply suggested patches manually only after human review.",
        ),
    ]
    categories = {suggestion.category for suggestion in suggestions}
    if "review_dynamic_usage" in categories:
        items.insert(1, ("dynamic", "Review dynamic PyProcore usage manually."))
    if "review_removed_endpoint_usage" in categories:
        items.insert(1, ("removed_endpoint", "Verify removed endpoint usage manually."))
    if categories & {"review_changed_parameters", "review_new_optional_parameters"}:
        items.insert(1, ("parameters", "Verify changed parameter usage manually."))
    return [PullRequestDraftChecklistItem(category=category, text=text) for category, text in items]


def _build_test_plan() -> list[str]:
    """Return safe test steps that avoid live Procore calls by default."""
    return [
        "Run the customer project's unit tests.",
        "Exercise CLI paths with mocked or sandbox fixture data only.",
        "Verify no Procore write endpoints or mutation actions are introduced.",
        "Verify environment variables remain managed by the customer.",
        "Verify no secrets, tokens, or authorization headers are committed.",
        "Review accepted edits and suggested diffs manually before applying them.",
    ]


def _build_risk_summary(
    suggestions: list[MigrationPatchSuggestion],
) -> PullRequestDraftRiskSummary:
    """Group migration suggestions by severity and manual uncertainty."""
    manual_categories = {"review_dynamic_usage", "manual_review_required"}
    unknown = [
        suggestion
        for suggestion in suggestions
        if suggestion.category in manual_categories or suggestion.severity == "unknown"
    ]
    remaining = [suggestion for suggestion in suggestions if suggestion not in unknown]
    return PullRequestDraftRiskSummary(
        high=[row for row in remaining if row.severity == "high"],
        medium=[row for row in remaining if row.severity == "medium"],
        low=[row for row in remaining if row.severity == "low"],
        unknown_manual_review=unknown,
    )


def _build_body_sections(
    migration_plan: MigrationPatchPlan,
    checklist: list[PullRequestDraftChecklistItem],
    test_plan: list[str],
) -> list[PullRequestDraftSection]:
    """Build the complete conservative pull-request body sections."""
    plan = migration_plan
    usages = plan.impact_report.scan_report.usages
    suggestions = plan.suggestions
    oas_provided = plan.impact_report.oas_comparison_provided
    usage_lines = [
        f"- `{usage.file_path}:{usage.line_number or '?'}` "
        f"{usage.usage_type}: `{usage.symbol}` ({usage.capability_family})"
        for usage in usages
    ]
    suggestion_lines = [
        f"- **{suggestion.category}** in `{suggestion.file_path}`: {suggestion.message}"
        for suggestion in suggestions
    ]
    drift_content = (
        f"Local OAS comparison found "
        f"{len(plan.impact_report.drift_report.added_endpoints)} added, "
        f"{len(plan.impact_report.drift_report.removed_endpoints)} removed, and "
        f"{len(plan.impact_report.drift_report.changed_parameters)} "
        "parameter-change records."
        if oas_provided and plan.impact_report.drift_report is not None
        else "No old/new local OAS comparison was provided; API drift remains unknown."
    )
    return [
        PullRequestDraftSection(
            heading="Summary",
            content=(
                "Review detected local PyProcore usage and conservative migration "
                "suggestions. This draft does not claim that fixes were applied."
            ),
        ),
        PullRequestDraftSection(
            heading="Why this review is needed",
            content=(
                "Local usage may need human review when PyProcore or related API "
                "metadata changes."
            ),
        ),
        PullRequestDraftSection(
            heading="Detected PyProcore usage",
            content="\n".join(usage_lines) or "- No PyProcore usage detected.",
        ),
        PullRequestDraftSection(
            heading="API drift summary",
            content=drift_content,
        ),
        PullRequestDraftSection(
            heading="Suggested migration review items",
            content="\n".join(suggestion_lines) or "- No migration suggestions.",
        ),
        PullRequestDraftSection(
            heading="Suggested patch artifacts",
            content=(
                "Any included diff is a non-applied review suggestion for a narrowly "
                "classified documentation or script reference. Apply nothing without "
                "manual review."
            ),
        ),
        PullRequestDraftSection(heading="Safety notes", content=_SAFETY_TEXT),
        PullRequestDraftSection(
            heading="Human-review checklist",
            content="\n".join(f"- [ ] {item.text}" for item in checklist),
        ),
        PullRequestDraftSection(
            heading="Test plan",
            content="\n".join(f"{index}. {step}" for index, step in enumerate(test_plan, 1)),
        ),
    ]
