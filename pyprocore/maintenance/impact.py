"""Relate local PyProcore usage to optional local OAS drift."""

from __future__ import annotations

from pathlib import Path

from pyprocore.catalog import OASCatalog, load_oas_catalog
from pyprocore.maintenance.codebase import scan_pyprocore_usage
from pyprocore.maintenance.drift import compare_oas_catalogs
from pyprocore.maintenance.models import (
    ApiDriftReport,
    ApiImpactFinding,
    ApiImpactReport,
    CodebaseScanOptions,
    ImpactedUsage,
    MigrationSuggestion,
    PyprocoreUsage,
)

LOCAL_ONLY_FAMILIES = {
    "analytics",
    "catalog",
    "discovery",
    "integrations",
    "maintenance",
    "plugins",
    "templates",
}


def analyze_codebase_api_impact(
    codebase_path: str | Path,
    old_oas_path: str | Path | None = None,
    new_oas_path: str | Path | None = None,
    *,
    options: CodebaseScanOptions | None = None,
) -> ApiImpactReport:
    """Analyze possible local codebase impact from optional local OAS drift.

    Args:
        codebase_path: Local customer codebase file or directory.
        old_oas_path: Optional earlier local OAS JSON file.
        new_oas_path: Optional newer local OAS JSON file.
        options: Optional bounded local scan settings.

    Returns:
        Human-review impact report. No customer files are modified.

    Raises:
        ValueError: If only one OAS path is provided.
    """
    if (old_oas_path is None) != (new_oas_path is None):
        raise ValueError("--old-oas and --new-oas must be provided together.")
    scan_report = scan_pyprocore_usage(codebase_path, options=options)
    if old_oas_path is None or new_oas_path is None:
        no_oas_impacted = [
            ImpactedUsage(
                usage=usage,
                severity="unknown",
                reasons=["No local OAS drift comparison was provided."],
            )
            for usage in scan_report.usages
        ]
        return ApiImpactReport(
            scanned_path=scan_report.scanned_path,
            scan_report=scan_report,
            findings=_findings_without_drift(scan_report.usages),
            impacted_usages=no_oas_impacted,
            migration_suggestions=[
                MigrationSuggestion(
                    capability_family="all",
                    priority="medium",
                    action=(
                        "Run impact-scan with both --old-oas and --new-oas for local "
                        "API drift comparison."
                    ),
                )
            ],
            notes=["No OAS comparison was provided; usage was scanned but API impact is unknown."],
        )

    drift_report = compare_oas_catalogs(old_oas_path, new_oas_path)
    old_catalog = load_oas_catalog(old_oas_path)
    new_catalog = load_oas_catalog(new_oas_path)
    changed_paths = _changed_paths(drift_report)
    path_areas = _path_area_map(old_catalog, new_catalog)
    changed_areas = {
        path_areas.get(path, "unknown")
        for path in changed_paths
        if path_areas.get(path, "unknown") != "unknown"
    }
    risky_paths = {change.path for change in drift_report.risky_changes}
    findings: list[ApiImpactFinding] = []
    impacted: list[ImpactedUsage] = []
    suggestions: list[MigrationSuggestion] = []
    for family in sorted({usage.capability_family for usage in scan_report.usages}):
        family_usages = [usage for usage in scan_report.usages if usage.capability_family == family]
        classification, message, related_paths = _classify_family(
            family,
            changed_areas,
            changed_paths,
            path_areas,
            risky_paths,
            family_usages,
        )
        severity = _severity_for_classification(classification)
        impacted_rows = [
            ImpactedUsage(usage=usage, severity=severity, reasons=[message])
            for usage in family_usages
        ]
        impacted.extend(impacted_rows)
        actions = _review_actions(classification, family)
        findings.append(
            ApiImpactFinding(
                classification=classification,
                capability_family=family,
                message=message,
                changed_endpoint_paths=related_paths,
                impacted_usages=impacted_rows,
                suggested_actions=actions,
            )
        )
        if classification in {
            "likely_affected",
            "possibly_affected",
            "deprecated_or_risky_usage",
            "unknown",
        }:
            suggestions.append(
                MigrationSuggestion(
                    capability_family=family,
                    priority="high" if classification == "likely_affected" else "medium",
                    action=actions[0],
                )
            )
    return ApiImpactReport(
        scanned_path=scan_report.scanned_path,
        scan_report=scan_report,
        drift_report=drift_report,
        oas_comparison_provided=True,
        findings=findings,
        impacted_usages=impacted,
        migration_suggestions=suggestions,
        notes=[
            "Possible impact is inferred from broad capability/resource families.",
            "Human review is required; this scanner does not edit or certify customer code.",
        ],
    )


def _findings_without_drift(usages: list[PyprocoreUsage]) -> list[ApiImpactFinding]:
    """Group no-comparison usage as unknown or local-only low risk."""
    findings: list[ApiImpactFinding] = []
    for family in sorted({usage.capability_family for usage in usages}):
        family_usages = [usage for usage in usages if usage.capability_family == family]
        local_only = family in LOCAL_ONLY_FAMILIES
        classification = "not_affected" if local_only else "unknown"
        message = (
            "Local-only capability usage has no direct Procore endpoint drift comparison."
            if local_only
            else "No OAS comparison was provided; API impact is unknown."
        )
        findings.append(
            ApiImpactFinding(
                classification=classification,
                capability_family=family,
                message=message,
                impacted_usages=[
                    ImpactedUsage(
                        usage=usage,
                        severity="low" if local_only else "unknown",
                        reasons=[message],
                    )
                    for usage in family_usages
                ],
                suggested_actions=["Review this usage manually if API behavior is a concern."],
            )
        )
    return findings


def _classify_family(
    family: str,
    changed_areas: set[str],
    changed_paths: set[str],
    path_areas: dict[str, str],
    risky_paths: set[str],
    usages: list[PyprocoreUsage],
) -> tuple[str, str, list[str]]:
    """Classify one broad usage family against drift areas."""
    if family == "unknown" or any(usage.dynamic for usage in usages):
        return (
            "unknown",
            "Dynamic or unmapped usage requires manual review.",
            [],
        )
    if family in LOCAL_ONLY_FAMILIES:
        return (
            "not_affected",
            "This usage is local metadata or exported-data processing, not a direct API call.",
            [],
        )
    related_paths = sorted(path for path in changed_paths if path_areas.get(path) == family)
    if family in changed_areas and any(path in risky_paths for path in related_paths):
        return (
            "deprecated_or_risky_usage",
            "Related endpoint metadata includes removed, changed, or risky operations.",
            related_paths,
        )
    if family in changed_areas:
        return (
            "likely_affected",
            "Detected usage maps directly to an endpoint area with local OAS drift.",
            related_paths,
        )
    if family == "workflows" and changed_areas:
        return (
            "possibly_affected",
            "Workflow helpers may depend on one or more changed endpoint areas.",
            sorted(changed_paths),
        )
    return (
        "not_affected",
        "No matching endpoint-area drift was found for this detected usage.",
        [],
    )


def _changed_paths(drift_report: ApiDriftReport) -> set[str]:
    """Return all endpoint paths represented by a typed drift report."""
    return {
        change.path
        for change in [
            *drift_report.added_endpoints,
            *drift_report.removed_endpoints,
            *drift_report.changed_methods,
            *drift_report.changed_parameters,
            *drift_report.changed_operation_ids,
        ]
    }


def _path_area_map(old_catalog: OASCatalog, new_catalog: OASCatalog) -> dict[str, str]:
    """Map endpoint paths to parsed catalog resource areas."""
    return {
        endpoint.path: endpoint.path_area
        for endpoint in [*old_catalog.endpoints, *new_catalog.endpoints]
    }


def _review_actions(classification: str, family: str) -> list[str]:
    """Return conservative manual-review actions."""
    if classification == "not_affected":
        return [f"No immediate API migration indicated for {family}; retain normal tests."]
    return [
        f"Review {family} usages against the changed local OAS endpoint metadata.",
        "Run mocked integration tests and verify official Procore documentation.",
        "Make any code changes manually; this scanner never edits customer files.",
    ]


def _severity_for_classification(classification: str) -> str:
    """Map impact classifications to report severity."""
    return {
        "likely_affected": "high",
        "deprecated_or_risky_usage": "high",
        "possibly_affected": "medium",
        "unknown": "unknown",
        "not_affected": "low",
    }[classification]
