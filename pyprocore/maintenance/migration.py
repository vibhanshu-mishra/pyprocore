"""Conservative local migration planning from PyProcore usage and OAS drift."""

from __future__ import annotations

import hashlib
from pathlib import Path

from pyprocore.maintenance.impact import LOCAL_ONLY_FAMILIES, analyze_codebase_api_impact
from pyprocore.maintenance.models import (
    ApiEndpointChange,
    ApiImpactReport,
    MigrationPatchFile,
    MigrationPatchPlan,
    MigrationPatchPlanOptions,
    MigrationPatchSuggestion,
    MigrationSafetyFinding,
    PyprocoreUsage,
)
from pyprocore.maintenance.patch_plan import render_unified_diff_suggestion


def build_migration_patch_plan(
    codebase_path: str | Path,
    old_oas_path: str | Path | None = None,
    new_oas_path: str | Path | None = None,
    options: MigrationPatchPlanOptions | None = None,
) -> MigrationPatchPlan:
    """Build a non-applied migration plan from local files and optional OAS drift.

    Args:
        codebase_path: User-selected local customer codebase.
        old_oas_path: Optional earlier local OAS JSON file.
        new_oas_path: Optional newer local OAS JSON file.
        options: Optional conservative planning settings.

    Returns:
        Typed migration patch plan requiring human review.
    """
    plan_options = options or MigrationPatchPlanOptions()
    impact = analyze_codebase_api_impact(
        codebase_path,
        old_oas_path=old_oas_path,
        new_oas_path=new_oas_path,
    )
    suggestions: list[MigrationPatchSuggestion] = []
    for usage in impact.scan_report.usages:
        usage_suggestions = _suggestions_for_usage(usage, impact)
        if not plan_options.include_no_action_suggestions:
            usage_suggestions = [
                suggestion
                for suggestion in usage_suggestions
                if suggestion.category != "no_action_recommended"
            ]
        suggestions.extend(usage_suggestions)

    if plan_options.include_suggested_diffs:
        suggestions = [_attach_safe_hunk(suggestion) for suggestion in suggestions]

    files = _group_suggestions_by_file(suggestions)
    return MigrationPatchPlan(
        scanned_path=impact.scanned_path,
        options=plan_options,
        impact_report=impact,
        impacted_files=sorted({suggestion.file_path for suggestion in suggestions}),
        suggestions=suggestions,
        files=files,
        manual_review_checklist=_manual_review_checklist(
            oas_comparison_provided=impact.oas_comparison_provided
        ),
        safety_findings=[
            MigrationSafetyFinding(
                severity="warning",
                code="suggestions_only",
                message=(
                    "Patch suggestions and diff hunks are review artifacts only. "
                    "No customer files are modified and no patches are applied."
                ),
            ),
            MigrationSafetyFinding(
                severity="info",
                code="local_only",
                message=(
                    "Only user-selected local files are read. No remote repository, "
                    "Procore, AI/model, MCP, tool, or git operation is used."
                ),
            ),
        ],
    )


def _suggestions_for_usage(
    usage: PyprocoreUsage,
    impact: ApiImpactReport,
) -> list[MigrationPatchSuggestion]:
    """Return conservative suggestion rows for one normalized usage."""
    if usage.dynamic:
        return [
            _suggestion(
                usage,
                category="review_dynamic_usage",
                severity="high",
                message=(
                    "Dynamic PyProcore access cannot be mapped to an exact API operation; "
                    "inspect this usage manually."
                ),
            )
        ]
    if usage.capability_family == "analytics":
        return [
            _suggestion(
                usage,
                category="local_analytics_no_api_change_needed",
                severity="low",
                message=(
                    "Local analytics reads exported data and has no direct Procore API "
                    "migration indicated."
                ),
            )
        ]

    finding = next(
        (row for row in impact.findings if row.capability_family == usage.capability_family),
        None,
    )
    related_paths = finding.changed_endpoint_paths if finding else []
    drift = impact.drift_report
    suggestions: list[MigrationPatchSuggestion] = []
    direct_drift_match = finding is not None and finding.classification in {
        "likely_affected",
        "deprecated_or_risky_usage",
    }
    if drift is not None and related_paths and direct_drift_match:
        removed = _matching_changes(drift.removed_endpoints, related_paths)
        parameters = _matching_changes(drift.changed_parameters, related_paths)
        if removed:
            suggestions.append(
                _suggestion(
                    usage,
                    category="review_removed_endpoint_usage",
                    severity="high",
                    message=(
                        "A related endpoint is absent from the newer local OAS file. "
                        "Verify the supported replacement manually."
                    ),
                    related_paths=[change.path for change in removed],
                )
            )
        for change in parameters:
            category = (
                "review_new_optional_parameters"
                if _only_adds_optional_parameters(change)
                else "review_changed_parameters"
            )
            suggestions.append(
                _suggestion(
                    usage,
                    category=category,
                    severity="medium" if category == "review_new_optional_parameters" else "high",
                    message=(
                        "Related endpoint parameter metadata changed in the local OAS "
                        "comparison; review names, locations, requirements, and types."
                    ),
                    related_paths=[change.path],
                )
            )

    if usage.usage_type == "cli":
        suggestions.append(
            _suggestion(
                usage,
                category="update_cli_command_docs",
                severity="medium",
                message=(
                    "Review this documented CLI command against current PyProcore help "
                    "before manually updating the document or script."
                ),
                related_paths=related_paths,
                exact_change_safe=Path(usage.file_path).suffix.lower() != ".py",
            )
        )
    elif usage.usage_type == "import":
        suggestions.append(
            _suggestion(
                usage,
                category="update_pyprocore_import_usage",
                severity="medium" if related_paths else "low",
                message=(
                    "Review this PyProcore import and its consumers; no automatic import "
                    "rewrite is proposed."
                ),
                related_paths=related_paths,
            )
        )

    if suggestions:
        return _deduplicate_suggestions(suggestions)
    if finding is not None and finding.classification in {"possibly_affected", "unknown"}:
        return [
            _suggestion(
                usage,
                category="manual_review_required",
                severity="medium",
                message=(
                    "This broad or unresolved usage may depend on changed API areas, "
                    "but no exact code change can be suggested safely."
                ),
                related_paths=related_paths,
            )
        ]
    if not impact.oas_comparison_provided and usage.capability_family not in LOCAL_ONLY_FAMILIES:
        return [
            _suggestion(
                usage,
                category="manual_review_required",
                severity="medium",
                message=(
                    "No local OAS comparison was provided, so API migration impact is "
                    "unknown and requires manual review."
                ),
            )
        ]
    return [
        _suggestion(
            usage,
            category="no_action_recommended",
            severity="low",
            message="No related local OAS drift was found for this detected usage.",
            related_paths=related_paths,
        )
    ]


def _suggestion(
    usage: PyprocoreUsage,
    *,
    category: str,
    severity: str,
    message: str,
    related_paths: list[str] | None = None,
    exact_change_safe: bool = False,
) -> MigrationPatchSuggestion:
    """Build one stable suggestion without retaining unredacted source."""
    identity = (f"{usage.file_path}:{usage.line_number}:{usage.symbol}:{category}").encode("utf-8")
    return MigrationPatchSuggestion(
        suggestion_id=hashlib.sha256(identity).hexdigest()[:16],
        category=category,
        severity=severity,
        message=message,
        file_path=usage.file_path,
        line_number=usage.line_number,
        capability_family=usage.capability_family,
        usage_type=usage.usage_type,
        source_snippet=usage.snippet,
        related_endpoint_paths=sorted(set(related_paths or [])),
        manual_review_only=True,
        exact_change_safe=exact_change_safe,
    )


def _matching_changes(
    changes: list[ApiEndpointChange],
    paths: list[str],
) -> list[ApiEndpointChange]:
    """Return drift changes related to a broad impact finding."""
    path_set = set(paths)
    return [change for change in changes if change.path in path_set]


def _only_adds_optional_parameters(change: ApiEndpointChange) -> bool:
    """Return whether parameter drift only introduces optional parameters."""
    before = {
        (parameter.name, parameter.location): parameter for parameter in change.parameters_before
    }
    after = {
        (parameter.name, parameter.location): parameter for parameter in change.parameters_after
    }
    if not before.keys() <= after.keys():
        return False
    additions = [after[key] for key in after.keys() - before.keys()]
    unchanged = all(before[key] == after[key] for key in before)
    return bool(additions) and unchanged and all(not parameter.required for parameter in additions)


def _attach_safe_hunk(
    suggestion: MigrationPatchSuggestion,
) -> MigrationPatchSuggestion:
    """Attach a suggested diff only when the renderer accepts the usage."""
    hunk = render_unified_diff_suggestion(suggestion)
    return suggestion.model_copy(update={"hunk": hunk})


def _group_suggestions_by_file(
    suggestions: list[MigrationPatchSuggestion],
) -> list[MigrationPatchFile]:
    """Group suggestions and safe hunks deterministically by customer file."""
    grouped: dict[str, list[MigrationPatchSuggestion]] = {}
    for suggestion in suggestions:
        grouped.setdefault(suggestion.file_path, []).append(suggestion)
    return [
        MigrationPatchFile(
            file_path=file_path,
            suggestions=rows,
            hunks=[row.hunk for row in rows if row.hunk is not None],
        )
        for file_path, rows in sorted(grouped.items())
    ]


def _deduplicate_suggestions(
    suggestions: list[MigrationPatchSuggestion],
) -> list[MigrationPatchSuggestion]:
    """Deduplicate repeated categories for one usage."""
    seen: set[tuple[str, str]] = set()
    result: list[MigrationPatchSuggestion] = []
    for suggestion in suggestions:
        key = (suggestion.category, ",".join(suggestion.related_endpoint_paths))
        if key not in seen:
            seen.add(key)
            result.append(suggestion)
    return result


def _manual_review_checklist(*, oas_comparison_provided: bool) -> list[str]:
    """Return the stable human-review checklist included in every plan."""
    checklist = [
        "Confirm each detected usage is active customer code.",
        "Verify affected endpoints in official Procore documentation.",
        "Review context IDs, permissions, pagination, and parameter requirements.",
        "Run mocked tests before making any customer-code change.",
        "Apply any accepted changes manually and review the resulting diff.",
        "Keep tokens, secrets, and authorization headers out of reports.",
    ]
    if not oas_comparison_provided:
        checklist.insert(
            1,
            "Provide old and new local OAS files before drawing API drift conclusions.",
        )
    return checklist
