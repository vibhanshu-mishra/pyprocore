"""Builders for local GC/Owner private app onboarding packets."""

from __future__ import annotations

from pyprocore.dmsa.models import (
    GcOwnerEmailTemplate,
    GcOwnerInstallationPacket,
    GcOwnerInstallationPacketOptions,
    GcOwnerInstallChecklist,
    GcOwnerInstallChecklistItem,
    GcOwnerPacketArtifact,
    GcOwnerPacketSection,
    GcOwnerPermissionRequest,
    GcOwnerPermissionRequestItem,
    GcOwnerSecurityStatement,
    GcOwnerTroubleshootingFinding,
    GcOwnerTroubleshootingGuide,
)

PACKET_ARTIFACTS = [
    GcOwnerPacketArtifact(
        filename="gc_owner_installation_packet.md",
        title="GC/Owner Installation Packet",
        description="Complete onboarding summary and review package.",
    ),
    GcOwnerPacketArtifact(
        filename="permission_request.md",
        title="Permission Request",
        description="Minimum required and conditional Read Only permissions.",
    ),
    GcOwnerPacketArtifact(
        filename="security_statement.md",
        title="Security Statement",
        description="Read-only safety, data handling, and revocation boundaries.",
    ),
    GcOwnerPacketArtifact(
        filename="admin_install_checklist.md",
        title="Admin Installation Checklist",
        description="GC/Owner and consultant review steps.",
    ),
    GcOwnerPacketArtifact(
        filename="email_templates.md",
        title="Email Templates",
        description="Copy-ready request, follow-up, troubleshooting, and offboarding text.",
    ),
    GcOwnerPacketArtifact(
        filename="troubleshooting_guide.md",
        title="Troubleshooting Guide",
        description="Likely causes and recommended reviews for common access issues.",
    ),
    GcOwnerPacketArtifact(
        filename="packet_metadata.json",
        title="Packet Metadata",
        description="Machine-readable local packet metadata.",
    ),
]


def build_rfi_submittal_permission_request(
    options: GcOwnerInstallationPacketOptions | None = None,
) -> GcOwnerPermissionRequest:
    """Build a minimum Read Only RFI/Submittal permission request."""
    selected = options or GcOwnerInstallationPacketOptions()
    conditional = []
    if selected.include_attachments:
        conditional.append(
            _permission(
                "RFI/Submittal attachments",
                "Read Only / visibility only",
                "Prepare attachment metadata manifests when payloads expose attachments.",
                False,
            )
        )
    if selected.use_webhooks:
        conditional.append(
            _permission(
                "RFI/Submittal created and updated events",
                "Event delivery only",
                "Notify a customer-controlled backend; polling remains a fallback.",
                False,
            )
        )
    if selected.include_linked_references:
        conditional.append(
            _permission(
                "Linked drawing/specification references",
                "Read Only",
                "Log linked reference metadata when present.",
                False,
            )
        )
    return GcOwnerPermissionRequest(
        title="Minimum RFI/Submittal Permission Request",
        summary=(
            "Request only the access needed for a read-only intake workflow on "
            "explicitly permitted projects."
        ),
        required_items=[
            _permission("RFIs", "Read Only", "Retrieve visible RFI records.", True),
            _permission(
                "Submittals",
                "Read Only",
                "Retrieve visible Submittal records.",
                True,
            ),
            _permission(
                "Permitted Projects",
                "Project visibility",
                "Limit access to projects explicitly selected by the GC/Owner.",
                True,
            ),
            _permission(
                "Project metadata",
                "Read Only",
                "Identify and label the selected projects.",
                True,
            ),
        ],
        conditional_items=conditional,
        excluded_actions=[
            "No create",
            "No edit or update",
            "No approve or reject",
            "No submit",
            "No close or reopen",
            "No delete",
            "No upload or import",
            "No payment or financial write actions",
        ],
        gc_owner_control_statement=(
            "The GC/Owner controls installation, permitted projects, tool "
            "permissions, attachment visibility, webhooks, and revocation."
        ),
    )


def build_gc_owner_security_statement(
    options: GcOwnerInstallationPacketOptions | None = None,
) -> GcOwnerSecurityStatement:
    """Build a conservative security and data handling statement."""
    selected = options or GcOwnerInstallationPacketOptions()
    return GcOwnerSecurityStatement(
        title=f"{selected.integration_name} Security Statement",
        statements=[
            "The integration is read-only.",
            "No Procore write actions are enabled.",
            "No automatic approvals, submissions, closes, deletes, or uploads occur.",
            "No automatic code edits, git operations, commits, or pull requests occur.",
            "No external AI/model APIs are called by default.",
            "MCP and Procore tool execution remain disabled.",
            "PyProcore does not install the app, create the DMSA, or grant access.",
        ],
        data_handling=[
            "The implementer/customer manages credentials in an appropriate secret store.",
            "Sync runs and outputs are controlled by the implementing backend.",
            "Logs and manifests should avoid unnecessary private project data.",
            "Attachment access depends on permissions and API payload availability.",
        ],
        control_and_revocation=[
            "The GC/Owner controls permitted projects and tool permissions.",
            "The GC/Owner can change or revoke access at any time.",
            "Webhook configuration and revocation remain under GC/Owner control.",
        ],
        disclaimer=(
            "This template is not a security certification or legal promise. "
            "The implementing organization must review its deployment."
        ),
    )


def build_gc_owner_email_templates(
    options: GcOwnerInstallationPacketOptions | None = None,
) -> list[GcOwnerEmailTemplate]:
    """Build professional placeholder-based onboarding email templates."""
    selected = options or GcOwnerInstallationPacketOptions()
    signature = f"Thank you,\n{selected.consultant_name}\n{selected.support_contact}"
    return [
        _email(
            "initial-request",
            "Initial request to GC/Owner admin",
            f"Read-only Procore integration request from {selected.consultant_name}",
            (
                f"Hello {selected.gc_owner_name} Admin,\n\n"
                f"We would like to request review of {selected.integration_name}. "
                "The requested first-version access is Read Only for RFIs and "
                "Submittals on projects you explicitly permit. PyProcore does not "
                "install the app, create the DMSA, or grant access.\n\n"
                f"{signature}"
            ),
        ),
        _email(
            "installed-follow-up",
            "Follow-up after installation",
            "Read-only Procore app installation follow-up",
            (
                "Hello,\n\nThank you for installing the private app. Please confirm "
                "the intended Permitted Projects and Read Only RFI/Submittal "
                f"permissions. Attachment access is optional.\n\n{signature}"
            ),
        ),
        _email(
            "permission-clarification",
            "Permission clarification request",
            "Clarification of read-only Procore permissions",
            (
                "Hello,\n\nCould you confirm whether the DMSA has Read Only access "
                "to RFIs and Submittals for the selected projects? No create, edit, "
                f"approval, submission, or upload permission is requested.\n\n{signature}"
            ),
        ),
        _email(
            "no-access",
            "Troubleshooting/no-project-access request",
            "Review requested: no permitted Procore projects visible",
            (
                "Hello,\n\nAuthentication appears configured, but no intended "
                "projects or records are visible. A likely cause is missing "
                "Permitted Projects or tool permission. Could you review the app "
                f"assignment without sharing credentials?\n\n{signature}"
            ),
        ),
        _email(
            "offboarding",
            "Revocation/offboarding note",
            "Request to revoke read-only Procore integration access",
            (
                "Hello,\n\nThe integration is no longer needed. Please revoke its "
                "project and app access according to your normal offboarding "
                f"process. We will retire customer-controlled credentials.\n\n{signature}"
            ),
        ),
    ]


def build_gc_owner_troubleshooting_guide(
    options: GcOwnerInstallationPacketOptions | None = None,
) -> GcOwnerTroubleshootingGuide:
    """Build likely-cause guidance without making live checks."""
    selected = options or GcOwnerInstallationPacketOptions()
    rows = [
        (
            "401",
            "Invalid credentials or token response",
            "Credential, token, or environment mismatch",
            "Review client credentials and production/sandbox URLs.",
        ),
        (
            "403",
            "Request is forbidden",
            "DMSA lacks project or tool permission",
            "Review app-company connection, Permitted Projects, and Read Only tool access.",
        ),
        (
            "404",
            "Project or record is not found",
            "Resource is not visible or the ID/environment is wrong",
            "Confirm project assignment, identifier, and environment.",
        ),
        (
            "empty_projects",
            "No projects returned",
            "Permitted Projects may not be assigned",
            "Confirm the GC/Owner assigned the intended projects.",
        ),
        (
            "empty_records",
            "No RFIs or Submittals returned",
            "No records exist or tool visibility is missing",
            "Confirm records exist and review RFIs/Submittals Read Only permissions.",
        ),
        (
            "missing_attachments",
            "Attachment metadata is absent",
            "Payload or permission does not expose attachments",
            "Review attachment visibility; availability is not guaranteed.",
        ),
        (
            "webhook_not_firing",
            "Expected event was not received",
            "Webhook may be unavailable, misconfigured, or delayed",
            "Review GC/Owner webhook setup and use polling fallback.",
        ),
        (
            "polling_no_updates",
            "Polling finds no new records",
            "No updates occurred or timestamp/project filters exclude them",
            "Review state timestamps, selected projects, and source records.",
        ),
        (
            "access_revoked",
            "Previously working access stops",
            "App, project, or tool access may have been revoked",
            "Ask the GC/Owner to review current authorization and revocation status.",
        ),
        (
            "projects_not_assigned",
            "Selected project is absent",
            "Project was not included in Permitted Projects",
            "Ask the GC/Owner to assign only the intended project if approved.",
        ),
    ]
    return GcOwnerTroubleshootingGuide(
        title=f"{selected.integration_name} Troubleshooting Guide",
        findings=[
            GcOwnerTroubleshootingFinding(
                code=code,
                symptom=symptom,
                likely_cause=cause,
                recommended_review=review,
            )
            for code, symptom, cause, review in rows
        ],
        disclaimer=(
            "These are likely causes and recommended reviews, not live findings "
            "or guarantees of access."
        ),
    )


def build_gc_owner_installation_packet(
    options: GcOwnerInstallationPacketOptions | None = None,
) -> GcOwnerInstallationPacket:
    """Build the complete local GC/Owner private app onboarding packet."""
    selected = options or GcOwnerInstallationPacketOptions()
    permission_request = build_rfi_submittal_permission_request(selected)
    security = build_gc_owner_security_statement(selected)
    emails = build_gc_owner_email_templates(selected)
    troubleshooting = build_gc_owner_troubleshooting_guide(selected)
    checklist = _build_checklist()
    return GcOwnerInstallationPacket(
        title="GC/Owner Private App Installation Packet",
        generated_for=selected.gc_owner_name,
        prepared_by=selected.consultant_name,
        executive_summary=(
            f"{selected.consultant_name} requests review of a read-only RFI and "
            "Submittal intake integration. The GC/Owner retains full control."
        ),
        sections=_packet_sections(selected),
        permission_request=permission_request,
        security_statement=security,
        install_checklist=checklist,
        email_templates=emails,
        troubleshooting_guide=troubleshooting,
        artifacts=list(PACKET_ARTIFACTS),
        support_contact=selected.support_contact,
        safety_boundaries=[
            "This packet is a local template/documentation aid.",
            "PyProcore does not install the app or create the DMSA.",
            "PyProcore does not grant or bypass project access.",
            "No Procore calls, remote fetches, or write actions occur.",
            "GC/Owner controls access, attachments, webhooks, and revocation.",
        ],
    )


def _packet_sections(
    options: GcOwnerInstallationPacketOptions,
) -> list[GcOwnerPacketSection]:
    return [
        GcOwnerPacketSection(
            title="Integration Purpose",
            summary="Normalize visible RFIs and Submittals into customer-controlled local logs.",
            items=["Read permitted records", "Track polling state", "Prepare attachment manifests"],
        ),
        GcOwnerPacketSection(
            title="What The Integration Does Not Do",
            summary="It does not modify Procore.",
            items=["No approvals or submissions", "No close/delete/upload", "No financial writes"],
        ),
        GcOwnerPacketSection(
            title="Installation Overview",
            summary=(
                "A GC/Owner admin reviews and installs the private app and " "authorizes its DMSA."
            ),
            items=["PyProcore does not install the app", "PyProcore does not create the DMSA"],
        ),
        GcOwnerPacketSection(
            title="Permitted Projects",
            summary="The GC/Owner selects the specific projects visible to the integration.",
            items=["Access is not guaranteed", "Assignments can be changed or revoked"],
        ),
        GcOwnerPacketSection(
            title="Attachments",
            summary="Attachment intake is conditional on permission and payload availability.",
            items=["Attachments are not guaranteed", f"Requested: {options.include_attachments}"],
        ),
        GcOwnerPacketSection(
            title="Webhooks And Polling",
            summary="Webhooks are optional; repeated read-only polling remains a fallback.",
            items=[
                "Webhook delivery is not guaranteed",
                f"Webhook requested: {options.use_webhooks}",
            ],
        ),
    ]


def _build_checklist() -> GcOwnerInstallChecklist:
    admin = [
        ("review", "Review packet", "Confirm purpose and least-privilege request."),
        ("install", "Install private app", "Use the approved App Version Key outside this packet."),
        (
            "authorize",
            "Authorize DMSA",
            "Create/authorize access through GC/Owner-controlled Procore administration.",
        ),
        ("projects", "Assign Permitted Projects", "Select only approved projects."),
        ("permissions", "Set Read Only permissions", "Grant RFIs and Submittals Read Only."),
        ("verify", "Verify controls", "Review attachments, webhooks, support, and revocation."),
    ]
    sender = [
        ("purpose", "Describe purpose", "Send the executive summary and permission request."),
        (
            "projects",
            "Identify intended projects",
            "Use placeholders or a secure channel for private project IDs.",
        ),
        ("contact", "Provide support contact", "Name the customer-controlled integration owner."),
        (
            "dry-run",
            "Validate locally",
            "Run mocked/local checks before any user-authored live integration.",
        ),
    ]
    return GcOwnerInstallChecklist(
        title="Private App Installation Checklists",
        admin_items=[
            GcOwnerInstallChecklistItem(
                item_id=item_id,
                title=title,
                description=description,
                owner="gc_owner",
            )
            for item_id, title, description in admin
        ],
        sender_items=[
            GcOwnerInstallChecklistItem(
                item_id=item_id,
                title=title,
                description=description,
                owner="consultant",
            )
            for item_id, title, description in sender
        ],
    )


def _permission(
    resource: str,
    access: str,
    reason: str,
    required: bool,
) -> GcOwnerPermissionRequestItem:
    return GcOwnerPermissionRequestItem(
        resource=resource,
        access=access,
        reason=reason,
        required=required,
    )


def _email(
    template_id: str,
    title: str,
    subject: str,
    body: str,
) -> GcOwnerEmailTemplate:
    return GcOwnerEmailTemplate(
        template_id=template_id,
        title=title,
        subject=subject,
        body=body,
    )
