"""JSON-compatible and Markdown rendering for DMSA planning artifacts."""

from __future__ import annotations

import json
from typing import Any

from pyprocore.dmsa.checklists import build_dmsa_permission_checklist
from pyprocore.dmsa.models import (
    DmsaConnectionProfileValidationReport,
    DmsaConnectionSummary,
    DmsaInstallationPacket,
    DmsaPermissionChecklist,
    DmsaPermissionDiagnosticReport,
    DmsaSmokeCheckPlan,
)


def build_dmsa_installation_packet(
    support_contact: str = "Contact your integration administrator.",
) -> DmsaInstallationPacket:
    """Build a plain-English GC/Owner installation packet."""
    return DmsaInstallationPacket(
        title="PyProcore read-only DMSA installation packet",
        what_it_does=[
            "Uses an existing GC/Owner-installed private app and DMSA client credentials.",
            "Reads permitted project metadata, RFIs, Submittals, and available "
            "attachment metadata.",
        ],
        requested_access=[
            "Only explicitly permitted projects.",
            "Read Only access to RFIs and Submittals.",
            "Related attachment visibility only when attachment sync is needed.",
        ],
        what_it_does_not_do=[
            "PyProcore does not create a DMSA in Procore or grant project access.",
            "No write actions are enabled.",
            "It does not create, edit, submit, approve, close, delete, or " "upload Procore data.",
        ],
        installation_summary=[
            "A GC/Owner Company Admin installs the private app using its App Version Key.",
            "The GC/Owner authorizes the DMSA and controls its permitted "
            "projects and permissions.",
        ],
        permitted_projects=[
            "Only projects assigned by the GC/Owner should be accessible.",
            "The GC/Owner can change or revoke access at any time.",
        ],
        attachment_access=[
            "Attachment sync depends on tool permission, attachment visibility, "
            "and API payload availability.",
            "Attachment availability is not guaranteed by the connection profile.",
        ],
        webhook_and_polling=[
            "RFI/Submittal event webhooks may be planned by the GC/Owner.",
            "Webhook availability and delivery are not guaranteed; a read-only "
            "polling fallback may be needed.",
        ],
        security_statement=[
            "Credentials remain in environment variables or the deployment "
            "secret store, not profile JSON.",
            "Generated profile, checklist, packet, smoke plan, and diagnostics "
            "are local metadata only.",
        ],
        troubleshooting={
            "401": "Review client credentials, token issuance, and production/sandbox URLs.",
            "403": "Review company/project assignment and Read Only tool permissions.",
            "404": "Confirm the resource ID, environment, and permitted-project assignment.",
            "no_projects": "Ask the GC/Owner to confirm permitted projects were assigned.",
            "no_rfis": "Confirm records exist and the DMSA has RFIs Read Only permission.",
            "no_submittals": (
                "Confirm records exist and the DMSA has Submittals Read Only permission."
            ),
        },
        support_contact=support_contact,
        permission_checklist=build_dmsa_permission_checklist(),
    )


def dmsa_report_to_json(report: Any) -> str:
    """Render a DMSA model as indented JSON."""
    if hasattr(report, "model_dump"):
        payload = report.model_dump(mode="json")
    else:
        payload = report
    return json.dumps(payload, indent=2, default=str)


def dmsa_validation_report_to_markdown(
    report: DmsaConnectionProfileValidationReport,
) -> str:
    """Render profile validation results as Markdown."""
    lines = [
        f"# DMSA Profile Validation: {report.profile_name}",
        "",
        f"**Valid:** {'Yes' if report.valid else 'No'}",
        "",
    ]
    if not report.findings:
        return "\n".join(lines + ["No structural findings."])
    lines.append("## Findings")
    for finding in report.findings:
        lines.extend(
            [
                "",
                f"### {finding.level.upper()}: {finding.code}",
                finding.message,
                f"**Recommended review:** {finding.recommended_review}",
            ]
        )
    return "\n".join(lines)


def dmsa_connection_summary_to_markdown(report: DmsaConnectionSummary) -> str:
    """Render a redacted connection summary as Markdown."""
    projects = ", ".join(str(item) for item in report.allowed_project_ids) or "None documented"
    lines = [
        f"# DMSA Connection: {report.profile_name}",
        "",
        f"- Company ID: {report.company_id or 'Not configured'}",
        f"- Allowed project IDs: {projects}",
        f"- API base: {report.api_base_url}",
        f"- Login URL: {report.login_url}",
        f"- Client ID env var: {report.credential_references['client_id_env_var']}",
        f"- Client secret env var: {report.credential_references['client_secret_env_var']}",
        f"- Token store backend: {report.token_store_backend}",
        "",
        "## Safety Boundaries",
    ]
    lines.extend(f"- {item}" for item in report.safety_boundaries)
    return "\n".join(lines)


def dmsa_permission_checklist_to_markdown(report: DmsaPermissionChecklist) -> str:
    """Render a GC/Owner permission checklist as Markdown."""
    lines = [f"# {report.title}", "", report.summary, ""]
    for item in report.items:
        requirement = "required" if item.required else "optional"
        lines.append(f"- [ ] **{item.title}** ({requirement}): {item.description}")
    return "\n".join(lines)


def dmsa_installation_packet_to_markdown(report: DmsaInstallationPacket) -> str:
    """Render an installation packet as Markdown."""
    sections: list[tuple[str, list[str]]] = [
        ("What This Integration Does", report.what_it_does),
        ("Requested Access", report.requested_access),
        ("What It Does Not Do", report.what_it_does_not_do),
        ("Installation Summary", report.installation_summary),
        ("Permitted Projects", report.permitted_projects),
        ("Attachment Access", report.attachment_access),
        ("Webhooks And Polling", report.webhook_and_polling),
        ("Security And Safety", report.security_statement),
    ]
    lines = [f"# {report.title}"]
    for title, values in sections:
        lines.extend(["", f"## {title}"])
        lines.extend(f"- {value}" for value in values)
    lines.extend(["", "## Troubleshooting"])
    lines.extend(f"- **{key}:** {value}" for key, value in report.troubleshooting.items())
    lines.extend(
        [
            "",
            "## Support",
            report.support_contact,
            "",
            dmsa_permission_checklist_to_markdown(report.permission_checklist),
        ]
    )
    return "\n".join(lines)


def dmsa_smoke_check_plan_to_markdown(report: DmsaSmokeCheckPlan) -> str:
    """Render a non-executing smoke-check plan as Markdown."""
    lines = [
        f"# DMSA Smoke-Check Plan: {report.profile_name}",
        "",
        "**Live execution enabled:** No",
        "",
        "This document is a plan only. It does not call Procore.",
    ]
    for item in report.items:
        lines.extend(
            [
                "",
                f"## {item.title}",
                f"- Purpose: {item.purpose}",
                f"- Expected result: {item.expected_result}",
                "- Access: Read only",
            ]
        )
    return "\n".join(lines)


def dmsa_permission_diagnostic_to_markdown(
    report: DmsaPermissionDiagnosticReport,
) -> str:
    """Render likely permission causes as Markdown."""
    lines = [
        f"# DMSA Permission Diagnostic: {report.context}",
        "",
        report.disclaimer,
        "",
    ]
    for finding in report.findings:
        lines.extend(
            [
                f"## {finding.code}",
                f"- Likely cause: {finding.likely_cause}",
                f"- Recommended review: {finding.recommended_review}",
                "",
            ]
        )
    return "\n".join(lines).rstrip()
