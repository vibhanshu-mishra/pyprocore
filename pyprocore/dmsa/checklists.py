"""GC/Owner checklists and safe read-only smoke plans for DMSA access."""

from __future__ import annotations

from pyprocore.dmsa.models import (
    DmsaConnectionProfile,
    DmsaPermissionChecklist,
    DmsaPermissionChecklistItem,
    DmsaSmokeCheckItem,
    DmsaSmokeCheckPlan,
)


def build_dmsa_permission_checklist() -> DmsaPermissionChecklist:
    """Build a GC/Owner-facing least-privilege installation checklist."""
    items = [
        (
            "install",
            "Install private app",
            "GC/Owner Company Admin installs the private app using its App Version Key.",
            True,
        ),
        (
            "projects",
            "Assign permitted projects",
            "GC/Owner selects only the projects this DMSA may access.",
            True,
        ),
        ("rfi", "RFIs: Read Only", "Grant the DMSA Read Only access to the RFIs tool.", True),
        (
            "submittal",
            "Submittals: Read Only",
            "Grant the DMSA Read Only access to the Submittals tool.",
            True,
        ),
        (
            "attachments",
            "Attachment visibility",
            "Confirm related RFI and Submittal attachments are visible "
            "if attachment sync is needed.",
            False,
        ),
        (
            "metadata",
            "Project metadata",
            "Allow minimum project metadata needed to identify permitted projects.",
            True,
        ),
        (
            "webhooks",
            "Optional webhooks",
            "Optionally configure RFI/Submittal created or updated webhooks; "
            "polling may still be needed.",
            False,
        ),
        (
            "revoke",
            "Revocation control",
            "GC/Owner can revoke app, project, or tool access at any time.",
            True,
        ),
        (
            "no-writes",
            "No write actions",
            "The app does not create, edit, submit, approve, close, delete, "
            "upload, or modify Procore data.",
            True,
        ),
    ]
    return DmsaPermissionChecklist(
        title="PyProcore DMSA permission checklist",
        summary="GC/Owner controls installation, permitted projects, and permissions.",
        items=[
            DmsaPermissionChecklistItem(
                item_id=item_id,
                title=title,
                description=description,
                required=required,
            )
            for item_id, title, description, required in items
        ],
    )


def build_dmsa_smoke_check_plan(
    profile: DmsaConnectionProfile,
) -> DmsaSmokeCheckPlan:
    """Build, but never execute, an explicit read-only DMSA smoke-check plan."""
    entries = [
        (
            "token",
            "Obtain client-credentials token",
            "Confirm configured credentials can obtain a token.",
            "A bearer token is returned without being printed.",
        ),
        (
            "projects",
            "List accessible projects",
            "Confirm the DMSA has permitted projects.",
            "Only GC/Owner-permitted projects are returned.",
        ),
        (
            "selected-project",
            "Verify selected project visibility",
            "Confirm documented project IDs are visible.",
            "Each intended project can be read.",
        ),
        (
            "rfis",
            "List project RFIs",
            "Confirm Read Only RFI permission.",
            "Visible RFIs are returned, or an empty authorized result is explained.",
        ),
        (
            "submittals",
            "List project Submittals",
            "Confirm Read Only Submittal permission.",
            "Visible Submittals are returned, or an empty authorized result is explained.",
        ),
        (
            "attachments",
            "Inspect attachment metadata",
            "Check whether attachment metadata is present when needed.",
            "Permitted attachment metadata is visible; availability is not guaranteed.",
        ),
    ]
    return DmsaSmokeCheckPlan(
        profile_name=profile.profile_name,
        selected_project_ids=profile.allowed_project_ids,
        items=[
            DmsaSmokeCheckItem(
                item_id=item_id,
                title=title,
                purpose=purpose,
                expected_result=expected,
            )
            for item_id, title, purpose, expected in entries
        ],
    )
