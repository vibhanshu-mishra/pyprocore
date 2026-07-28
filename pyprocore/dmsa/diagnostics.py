"""Local permission diagnostics for supplied DMSA response summaries."""

from __future__ import annotations

from pyprocore.dmsa.models import (
    DmsaPermissionDiagnosticFinding,
    DmsaPermissionDiagnosticReport,
)


def diagnose_dmsa_permission_issue(
    *,
    status_code: int | None = None,
    context: str = "general",
    empty_result: bool = False,
    missing_attachments: bool = False,
) -> DmsaPermissionDiagnosticReport:
    """Map local response metadata to non-certain permission guidance."""
    findings: list[DmsaPermissionDiagnosticFinding] = []

    def add(code: str, likely_cause: str, review: str) -> None:
        findings.append(
            DmsaPermissionDiagnosticFinding(
                code=code,
                likely_cause=likely_cause,
                recommended_review=review,
            )
        )

    if status_code == 401:
        add(
            "unauthorized",
            "The client credentials or issued token may be invalid, expired, "
            "or for another environment.",
            "Review credential environment variables, auth URL, API environment, "
            "and token rotation.",
        )
    elif status_code == 403:
        add(
            "forbidden",
            "The DMSA likely lacks permission for the requested company, " "project, or tool.",
            "Ask the GC/Owner to review app installation, permitted projects, "
            "and Read Only tool permissions.",
        )
    elif status_code == 404:
        add(
            "not_found",
            "The project/resource ID may be wrong, or the DMSA may not be "
            "assigned to that project.",
            "Confirm IDs and environment, then review the GC/Owner "
            "permitted-project assignment.",
        )

    normalized_context = context.casefold().replace("-", "_")
    if empty_result and normalized_context in {"projects", "project"}:
        add(
            "empty_projects",
            "No permitted projects may be assigned to the DMSA.",
            "Ask the GC/Owner to confirm at least one permitted project is assigned.",
        )
    elif empty_result and normalized_context in {"rfis", "rfi", "submittals", "submittal"}:
        tool = "RFIs" if "rfi" in normalized_context else "Submittals"
        add(
            "empty_tool_results",
            f"No {tool} records may be visible, or the DMSA may lack {tool} tool permission.",
            f"Confirm records exist and review the DMSA Read Only permission for {tool}.",
        )

    if missing_attachments:
        add(
            "missing_attachment_metadata",
            "Attachment permissions or this API payload may not expose attachment metadata.",
            "Review attachment visibility and inspect the documented response "
            "shape; availability is not guaranteed.",
        )

    if not findings:
        add(
            "insufficient_context",
            "The supplied local response summary does not identify a likely permission issue.",
            "Provide a status code or empty-result/attachment context without including secrets.",
        )
    return DmsaPermissionDiagnosticReport(
        context=context,
        status_code=status_code,
        findings=findings,
    )
