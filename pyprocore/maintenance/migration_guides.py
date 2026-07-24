"""Build local, human-review migration guides from compatibility metadata."""

from __future__ import annotations

import json
from pathlib import Path, PurePosixPath

from pyprocore.core.exceptions import ValidationError
from pyprocore.maintenance.compatibility import (
    analyze_codebase_compatibility_with_contract,
    build_current_compatibility_contract,
    diff_compatibility_contracts,
    load_compatibility_contract,
)
from pyprocore.maintenance.models import (
    ApiCompatibilityContract,
    ApiCompatibilityDiffReport,
    CodebaseCompatibilityReport,
    MigrationGuide,
    MigrationGuideAction,
    MigrationGuideArtifact,
    MigrationGuideBreakingChange,
    MigrationGuideDeprecation,
    MigrationGuideFeatureAddition,
    MigrationGuideItem,
    MigrationGuideKnownGap,
    MigrationGuideOptions,
    MigrationGuideReport,
    MigrationGuideRisk,
    MigrationGuideSection,
    MigrationGuideValidationFinding,
)

_SAFETY_NOTES = [
    "Local metadata only; no Procore calls or remote fetches are performed.",
    "No customer code is edited and no patch is applied.",
    "No git operation, GitHub API call, commit, or pull request is performed.",
    "No MCP/tool execution or external AI/model call is performed.",
    "This guide does not certify production compatibility; human review is required.",
]


def build_migration_guide(
    from_contract_path: str | Path | None = None,
    to_contract_path: str | Path | None = None,
    codebase_path: str | Path | None = None,
    options: MigrationGuideOptions | None = None,
) -> MigrationGuide:
    """Build a structured local migration guide without changing any files.

    Args:
        from_contract_path: Optional older local JSON compatibility contract.
        to_contract_path: Optional newer local JSON compatibility contract.
        codebase_path: Optional local codebase to inspect without execution.
        options: Deterministic guide presentation options.

    Returns:
        A typed migration guide requiring human review.

    Raises:
        ValidationError: If only one contract is supplied or a codebase scan has
            no target contract.
    """
    guide_options = options or MigrationGuideOptions()
    if bool(from_contract_path) != bool(to_contract_path):
        raise ValidationError("Both --from-contract and --to-contract are required together.")
    if codebase_path is not None and to_contract_path is None:
        raise ValidationError("A codebase compatibility review requires --to-contract.")

    target = (
        load_compatibility_contract(to_contract_path)
        if to_contract_path is not None
        else build_current_compatibility_contract()
    )
    diff = (
        diff_compatibility_contracts(from_contract_path, to_contract_path)
        if from_contract_path is not None and to_contract_path is not None
        else None
    )
    source = (
        load_compatibility_contract(from_contract_path) if from_contract_path is not None else None
    )
    codebase_impact = (
        analyze_codebase_compatibility_with_contract(codebase_path, to_contract_path)
        if codebase_path is not None and to_contract_path is not None
        else None
    )

    additions = _feature_additions(diff, target)
    breaking = _breaking_changes(diff)
    deprecations = _deprecations(diff)
    gaps = [
        MigrationGuideKnownGap(
            family=gap.family,
            status=gap.status,
            reason=gap.reason,
        )
        for gap in target.known_gaps
    ]
    risks = _risks(diff, codebase_impact)
    overall_risk = _overall_risk(risks)
    sections = _sections(diff, additions, breaking, deprecations, gaps, codebase_impact)
    comparison_provided = diff is not None
    summary = (
        f"Local compatibility review from PyProcore {source.pyprocore_version} "
        f"to {target.pyprocore_version}."
        if source is not None
        else (
            f"General migration readiness guide for PyProcore {target.pyprocore_version}; "
            "no previous/target contract comparison was provided."
        )
    )
    return MigrationGuide(
        title=guide_options.title,
        generated_at=guide_options.generated_at,
        from_version=source.pyprocore_version if source else None,
        to_version=target.pyprocore_version,
        comparison_provided=comparison_provided,
        summary=summary,
        overall_risk=overall_risk,
        sections=sections,
        feature_additions=additions,
        breaking_changes=breaking,
        deprecations=deprecations,
        known_gaps=gaps,
        risks=risks,
        recommended_upgrade_checklist=_upgrade_checklist(diff, codebase_impact),
        manual_verification_checklist=_verification_checklist(codebase_impact),
        suggested_test_plan=_test_plan(codebase_impact),
        maintainer_notes=[
            "Review changelog and compatibility metadata before communicating an upgrade.",
            "Confirm deprecated and removed helpers have clear replacement guidance.",
            "Keep risky or ambiguous endpoint families deferred until manually verified.",
        ],
        safety_notes=_SAFETY_NOTES,
        codebase_impact=codebase_impact,
        findings=(
            [
                MigrationGuideValidationFinding(
                    severity="info",
                    code="no_contract_comparison",
                    message="No previous/target compatibility contract comparison was provided.",
                )
            ]
            if not comparison_provided
            else []
        ),
    )


def write_migration_guide_artifacts(
    guide: MigrationGuide,
    output_dir: str | Path,
    *,
    dry_run: bool = True,
    overwrite: bool = False,
) -> MigrationGuideReport:
    """Plan or write fixed migration-guide artifacts under one output directory."""
    from pyprocore.maintenance.migration_guide_reports import (
        build_migration_guide_artifacts,
    )

    root = Path(output_dir).expanduser().resolve()
    artifacts = build_migration_guide_artifacts(guide)
    destinations: list[tuple[MigrationGuideArtifact, Path]] = []
    for artifact in artifacts:
        relative_path = _validate_artifact_path(artifact.relative_path)
        destination = (root / relative_path).resolve()
        if not destination.is_relative_to(root):
            raise ValidationError(
                f"Migration guide artifact must remain inside output directory: {relative_path}"
            )
        if destination.exists() and not overwrite:
            raise ValidationError(
                "Migration guide artifact already exists; use --overwrite explicitly: "
                f"{destination}"
            )
        destinations.append((artifact, destination))
    if dry_run:
        return MigrationGuideReport(
            guide=guide,
            output_dir=str(root),
            dry_run=True,
            artifacts=artifacts,
            planned_files=[str(path) for _, path in destinations],
            findings=[
                MigrationGuideValidationFinding(
                    severity="info",
                    code="dry_run",
                    message="Dry-run complete; no artifact or customer file was written.",
                )
            ],
        )

    written_files = []
    for artifact, destination in destinations:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(artifact.content, encoding="utf-8")
        written_files.append(str(destination))
    return MigrationGuideReport(
        guide=guide,
        output_dir=str(root),
        dry_run=False,
        artifacts=artifacts,
        written_files=written_files,
        findings=[
            MigrationGuideValidationFinding(
                severity="info",
                code="artifacts_written",
                message="Artifacts were written only inside the selected output directory.",
            )
        ],
    )


def _feature_additions(
    diff: ApiCompatibilityDiffReport | None,
    target: ApiCompatibilityContract,
) -> list[MigrationGuideFeatureAddition]:
    """Return newly declared capabilities."""
    if diff is None:
        return []
    resources = {resource.name: resource for resource in target.resources}
    return [
        MigrationGuideFeatureAddition(
            name=name,
            category=resources[name].category,
            risk_level="informational" if resources[name].read_only else "manual_review",
        )
        for name in diff.added_resource_families
    ]


def _breaking_changes(
    diff: ApiCompatibilityDiffReport | None,
) -> list[MigrationGuideBreakingChange]:
    """Return removed resource and CLI capabilities."""
    if diff is None:
        return []
    return [
        *[
            MigrationGuideBreakingChange(
                subject=name,
                change_type="removed_resource_family",
                migration_note="Review and replace all usage before upgrading.",
            )
            for name in diff.removed_resource_families
        ],
        *[
            MigrationGuideBreakingChange(
                subject=name,
                change_type="removed_cli_group",
                migration_note="Review scripts and documentation using this CLI group.",
            )
            for name in diff.removed_cli_groups
        ],
    ]


def _deprecations(
    diff: ApiCompatibilityDiffReport | None,
) -> list[MigrationGuideDeprecation]:
    """Return newly introduced deprecations."""
    if diff is None:
        return []
    return [
        MigrationGuideDeprecation(
            helper=item.helper,
            migration_note=item.migration_note,
        )
        for item in diff.added_deprecations
    ]


def _risks(
    diff: ApiCompatibilityDiffReport | None,
    codebase_impact: CodebaseCompatibilityReport | None,
) -> list[MigrationGuideRisk]:
    """Classify migration risk conservatively."""
    risks: list[MigrationGuideRisk] = []
    if diff is not None:
        risks.extend(
            MigrationGuideRisk(
                level="breaking",
                subject=name,
                reason="A previously declared resource family was removed.",
            )
            for name in diff.removed_resource_families
        )
        risks.extend(
            MigrationGuideRisk(
                level="breaking",
                subject=name,
                reason="A previously declared CLI group was removed.",
            )
            for name in diff.removed_cli_groups
        )
        risks.extend(
            MigrationGuideRisk(
                level="medium",
                subject=item.helper,
                reason="A new deprecation requires migration review.",
            )
            for item in diff.added_deprecations
        )
        risks.extend(
            MigrationGuideRisk(
                level=(
                    "high" if _boundary_weakened(change.before, change.after) else "informational"
                ),
                subject=change.subject,
                reason=(
                    "A safety boundary may have weakened."
                    if _boundary_weakened(change.before, change.after)
                    else "A safety boundary remained safe or became stricter."
                ),
            )
            for change in diff.changed_safety_boundaries
        )
        risks.extend(
            MigrationGuideRisk(
                level="low",
                subject=name,
                reason="A new read-only or local capability was added.",
            )
            for name in [*diff.added_resource_families, *diff.added_cli_groups]
        )
    if codebase_impact is not None:
        impact = codebase_impact
        for usage in impact.scan_report.usages:
            if usage.dynamic:
                risks.append(
                    MigrationGuideRisk(
                        level="manual_review",
                        subject=f"{usage.file_path}:{usage.symbol}",
                        reason="Dynamic usage cannot be resolved statically.",
                    )
                )
    return risks or [
        MigrationGuideRisk(
            level="informational",
            subject="general_readiness",
            reason="No compatibility comparison was provided; perform a manual review.",
        )
    ]


def _sections(
    diff: ApiCompatibilityDiffReport | None,
    additions: list[MigrationGuideFeatureAddition],
    breaking: list[MigrationGuideBreakingChange],
    deprecations: list[MigrationGuideDeprecation],
    gaps: list[MigrationGuideKnownGap],
    codebase_impact: CodebaseCompatibilityReport | None,
) -> list[MigrationGuideSection]:
    """Build ordered human-readable guide sections."""
    sections = [
        _section(
            "New capabilities",
            "New read-only or local capabilities declared by the target contract.",
            [
                _item("feature_addition", row.name, row.category, row.risk_level)
                for row in additions
            ],
        ),
        _section(
            "Breaking changes",
            "Removed capabilities that require review before upgrading.",
            [
                _item(row.change_type, row.subject, row.migration_note, row.risk_level)
                for row in breaking
            ],
        ),
        _section(
            "Deprecations",
            "Helpers newly marked deprecated by the target contract.",
            [
                _item("deprecation", row.helper, row.migration_note, row.risk_level)
                for row in deprecations
            ],
        ),
        _section(
            "Known gaps",
            "Deferred or ambiguous capability families remain manual-review items.",
            [_item("known_gap", row.family, row.reason, row.risk_level) for row in gaps],
        ),
    ]
    if diff is not None:
        sections.extend(
            [
                _section(
                    "CLI changes",
                    "CLI groups added or removed by the compatibility contract.",
                    [
                        *[
                            _item(
                                "added_cli_group",
                                name,
                                "New CLI group; no automatic migration is performed.",
                                "informational",
                            )
                            for name in diff.added_cli_groups
                        ],
                        *[
                            _item(
                                "removed_cli_group",
                                name,
                                "Review local scripts before upgrading.",
                                "breaking",
                            )
                            for name in diff.removed_cli_groups
                        ],
                    ],
                ),
                _section(
                    "Safety boundary changes",
                    "Every safety-boundary change requires explicit human review.",
                    [
                        _item(
                            "safety_boundary",
                            row.subject,
                            f"{row.before!r} to {row.after!r}",
                            (
                                "high"
                                if _boundary_weakened(row.before, row.after)
                                else "informational"
                            ),
                        )
                        for row in diff.changed_safety_boundaries
                    ],
                ),
            ]
        )
    sections.append(
        _section(
            "Local maintenance workflow",
            "Migration guides are generated locally and never apply changes.",
            [
                _item(
                    "local_only",
                    "maintenance_workflow",
                    "Review compatibility contracts, guide output, tests, and changelog manually.",
                    "informational",
                )
            ],
        )
    )
    if codebase_impact is not None:
        impact = codebase_impact
        sections.append(
            _section(
                "Codebase-specific impact",
                f"Local scan of {impact.scanned_path}; no files were modified.",
                [
                    *[
                        _item(
                            "deprecated_usage",
                            row.symbol or row.family or "unknown",
                            row.migration_note or row.message,
                            "medium",
                        )
                        for row in impact.deprecated
                    ],
                    *[
                        _item(
                            "manual_review_usage",
                            row.symbol or row.family or "unknown",
                            row.message,
                            "manual_review",
                        )
                        for row in impact.unknown_manual_review
                    ],
                ],
            )
        )
    return sections


def _section(
    title: str,
    summary: str,
    items: list[MigrationGuideItem],
) -> MigrationGuideSection:
    """Build one guide section."""
    return MigrationGuideSection(title=title, summary=summary, items=items)


def _item(category: str, subject: str, summary: str, risk: str) -> MigrationGuideItem:
    """Build one normalized guide item."""
    return MigrationGuideItem(
        category=category,
        subject=subject,
        summary=summary,
        risk_level=risk,
        actions=[
            MigrationGuideAction(
                action="Review this item and record the migration decision.",
                priority=risk,
            )
        ],
    )


def _overall_risk(risks: list[MigrationGuideRisk]) -> str:
    """Return the highest ordered guide risk."""
    order = {
        "informational": 0,
        "low": 1,
        "manual_review": 2,
        "medium": 3,
        "high": 4,
        "breaking": 5,
    }
    return max(risks, key=lambda row: order[row.level]).level


def _boundary_weakened(before: str | None, after: str | None) -> bool:
    """Conservatively identify a potentially weaker safety status."""
    safe = {"disabled", "none", "discovery_only", "required"}
    return before in safe and after not in safe


def _upgrade_checklist(
    diff: ApiCompatibilityDiffReport | None,
    codebase_impact: CodebaseCompatibilityReport | None,
) -> list[str]:
    """Return a human-owned upgrade checklist."""
    rows = [
        "Read the release changelog and this migration guide.",
        "Review every breaking, high-risk, deprecated, and manual-review item.",
        "Confirm safety boundaries remain acceptable for the deployment.",
        "Upgrade in an isolated environment and retain a rollback plan.",
    ]
    if diff and diff.removed_cli_groups:
        rows.append("Update scripts referencing removed CLI groups.")
    if codebase_impact is not None:
        rows.append("Review every codebase-specific finding; no source edit was made.")
    return rows


def _verification_checklist(
    codebase_impact: CodebaseCompatibilityReport | None,
) -> list[str]:
    """Return checks that cannot be safely automated here."""
    rows = [
        "Confirm imported helpers and CLI commands still match documented interfaces.",
        "Verify deprecation replacements against maintained public documentation.",
        "Confirm known gaps do not affect the intended workflow.",
        "Review logs and output for secrets before sharing artifacts.",
    ]
    if codebase_impact is not None and any(
        usage.dynamic for usage in codebase_impact.scan_report.usages
    ):
        rows.append("Manually inspect dynamic PyProcore usage that static analysis cannot resolve.")
    return rows


def _test_plan(codebase_impact: CodebaseCompatibilityReport | None) -> list[str]:
    """Return a local test plan that avoids live Procore requests."""
    rows = [
        "Run unit tests with mocked transports and local fixtures.",
        "Run formatting, lint, type checking, and documentation truth checks.",
        "Validate compatibility contracts and review their diff.",
        "Exercise affected CLI parsing without credentials or network access.",
    ]
    if codebase_impact is not None:
        rows.append("Add focused tests for each impacted static or dynamic usage.")
    return rows


def _validate_artifact_path(value: str) -> Path:
    """Reject absolute, empty, and traversing artifact paths."""
    pure_path = PurePosixPath(value)
    if (
        pure_path.is_absolute()
        or ".." in pure_path.parts
        or not pure_path.parts
        or any(part in {"", "."} for part in pure_path.parts)
    ):
        raise ValidationError(f"Unsafe migration guide artifact path: {value}")
    return Path(*pure_path.parts)


def migration_guide_metadata(guide: MigrationGuide) -> str:
    """Return deterministic artifact metadata JSON."""
    payload = {
        "schema_version": guide.schema_version,
        "from_version": guide.from_version,
        "to_version": guide.to_version,
        "overall_risk": guide.overall_risk,
        "human_review_required": True,
        "customer_files_modified": False,
        "patches_applied": False,
        "git_operations_enabled": False,
        "github_api_calls_enabled": False,
        "pull_request_opened": False,
    }
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"
