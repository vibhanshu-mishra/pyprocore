"""Render and write local GC/Owner onboarding packet artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pyprocore.core.exceptions import ValidationError
from pyprocore.dmsa.models import (
    GcOwnerEmailTemplate,
    GcOwnerInstallationPacket,
    GcOwnerInstallChecklist,
    GcOwnerPacketWriteResult,
    GcOwnerPermissionRequest,
    GcOwnerSecurityStatement,
    GcOwnerTroubleshootingGuide,
)


def gc_owner_packet_to_json(value: Any) -> str:
    """Render packet metadata as indented JSON."""
    payload = value.model_dump(mode="json") if hasattr(value, "model_dump") else value
    return json.dumps(payload, indent=2, sort_keys=True, default=str)


def gc_owner_permission_request_to_markdown(
    request: GcOwnerPermissionRequest,
) -> str:
    """Render the minimum permission request as Markdown."""
    lines = [
        f"# {request.title}",
        "",
        request.summary,
        "",
        "## Required",
    ]
    lines.extend(_permission_lines(request.required_items))
    lines.extend(["", "## Conditional"])
    lines.extend(_permission_lines(request.conditional_items) or ["- None"])
    lines.extend(["", "## Explicitly Excluded"])
    lines.extend(f"- {item}" for item in request.excluded_actions)
    lines.extend(["", request.gc_owner_control_statement])
    return "\n".join(lines) + "\n"


def gc_owner_security_statement_to_markdown(
    statement: GcOwnerSecurityStatement,
) -> str:
    """Render the security statement as Markdown."""
    return _sectioned_markdown(
        statement.title,
        [
            ("Safety Commitments", statement.statements),
            ("Data Handling", statement.data_handling),
            ("Control And Revocation", statement.control_and_revocation),
        ],
        footer=statement.disclaimer,
    )


def gc_owner_install_checklist_to_markdown(
    checklist: GcOwnerInstallChecklist,
) -> str:
    """Render admin and sender checklists as Markdown."""
    lines = [f"# {checklist.title}", "", "## GC/Owner Admin"]
    lines.extend(f"- [ ] **{item.title}:** {item.description}" for item in checklist.admin_items)
    lines.extend(["", "## Consultant/Subcontractor"])
    lines.extend(f"- [ ] **{item.title}:** {item.description}" for item in checklist.sender_items)
    return "\n".join(lines) + "\n"


def gc_owner_email_templates_to_markdown(
    templates: list[GcOwnerEmailTemplate],
) -> str:
    """Render copy-ready email templates as Markdown."""
    lines = ["# GC/Owner Email Templates", "", "Local templates only; review before sending."]
    for template in templates:
        lines.extend(
            [
                "",
                f"## {template.title}",
                "",
                f"**Subject:** {template.subject}",
                "",
                "```text",
                template.body,
                "```",
            ]
        )
    return "\n".join(lines) + "\n"


def gc_owner_troubleshooting_guide_to_markdown(
    guide: GcOwnerTroubleshootingGuide,
) -> str:
    """Render cautious troubleshooting guidance as Markdown."""
    lines = [
        f"# {guide.title}",
        "",
        guide.disclaimer,
        "",
        "| Code | Symptom | Likely cause | Recommended review |",
        "| --- | --- | --- | --- |",
    ]
    lines.extend(
        f"| {item.code} | {item.symptom} | {item.likely_cause} | " f"{item.recommended_review} |"
        for item in guide.findings
    )
    return "\n".join(lines) + "\n"


def gc_owner_installation_packet_to_markdown(
    packet: GcOwnerInstallationPacket,
) -> str:
    """Render the complete GC/Owner installation packet as Markdown."""
    lines = [
        f"# {packet.title}",
        "",
        "**Local template/documentation aid only.**",
        "",
        f"- Prepared for: {packet.generated_for}",
        f"- Prepared by: {packet.prepared_by}",
        f"- Support: {packet.support_contact}",
        "",
        "## Executive Summary",
        "",
        packet.executive_summary,
    ]
    for section in packet.sections:
        lines.extend(["", f"## {section.title}", "", section.summary])
        lines.extend(f"- {item}" for item in section.items)
    lines.extend(
        [
            "",
            "## Safety Boundaries",
            *[f"- {item}" for item in packet.safety_boundaries],
            "",
            gc_owner_permission_request_to_markdown(packet.permission_request),
            gc_owner_security_statement_to_markdown(packet.security_statement),
            gc_owner_install_checklist_to_markdown(packet.install_checklist),
            gc_owner_email_templates_to_markdown(packet.email_templates),
            gc_owner_troubleshooting_guide_to_markdown(packet.troubleshooting_guide),
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def gc_owner_packet_write_result_to_markdown(
    result: GcOwnerPacketWriteResult,
) -> str:
    """Render a packet write or dry-run summary."""
    paths = result.planned_files if result.dry_run else result.written_files
    lines = [
        "# GC/Owner Packet Artifact Summary",
        "",
        f"- Output directory: `{result.output_dir}`",
        f"- Dry-run: {'yes' if result.dry_run else 'no'}",
        "- Procore calls: none",
        "- App installation performed: no",
        "- DMSA created: no",
        "- Project access granted: no",
        "- Write actions enabled: no",
        "",
        "## Artifacts",
    ]
    lines.extend(f"- `{path}`" for path in paths)
    return "\n".join(lines) + "\n"


def write_gc_owner_installation_packet(
    packet: GcOwnerInstallationPacket,
    output_dir: str | Path,
    *,
    dry_run: bool = True,
    overwrite: bool = False,
) -> GcOwnerPacketWriteResult:
    """Plan or write packet artifacts inside one local output directory."""
    root = _safe_root(output_dir)
    destinations = [
        (artifact.filename, _inside(root, artifact.filename)) for artifact in packet.artifacts
    ]
    if dry_run:
        return GcOwnerPacketWriteResult(
            output_dir=str(root),
            dry_run=True,
            planned_files=[name for name, _ in destinations],
        )
    existing = [path for _, path in destinations if path.exists()]
    if existing and not overwrite:
        raise ValidationError(
            "Refusing to overwrite existing GC/Owner packet artifacts: "
            + ", ".join(str(path) for path in existing)
        )
    content = _artifact_content(packet)
    root.mkdir(parents=True, exist_ok=True)
    written = []
    for name, destination in destinations:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(content[name].rstrip() + "\n", encoding="utf-8")
        written.append(name)
    return GcOwnerPacketWriteResult(
        output_dir=str(root),
        dry_run=False,
        planned_files=[name for name, _ in destinations],
        written_files=written,
    )


def _artifact_content(packet: GcOwnerInstallationPacket) -> dict[str, str]:
    return {
        "gc_owner_installation_packet.md": gc_owner_installation_packet_to_markdown(packet),
        "permission_request.md": gc_owner_permission_request_to_markdown(packet.permission_request),
        "security_statement.md": gc_owner_security_statement_to_markdown(packet.security_statement),
        "admin_install_checklist.md": gc_owner_install_checklist_to_markdown(
            packet.install_checklist
        ),
        "email_templates.md": gc_owner_email_templates_to_markdown(packet.email_templates),
        "troubleshooting_guide.md": gc_owner_troubleshooting_guide_to_markdown(
            packet.troubleshooting_guide
        ),
        "packet_metadata.json": gc_owner_packet_to_json(packet),
    }


def _safe_root(output_dir: str | Path) -> Path:
    candidate = Path(output_dir).expanduser()
    if ".." in candidate.parts:
        raise ValidationError("Path traversal is not allowed for GC/Owner packet output.")
    return candidate.resolve()


def _inside(root: Path, relative_path: str) -> Path:
    candidate = (root / relative_path).resolve()
    if not candidate.is_relative_to(root):
        raise ValidationError("Packet artifacts must remain inside output_dir.")
    return candidate


def _permission_lines(items: list[Any]) -> list[str]:
    return [
        f"- **{item.resource}: {item.access}** - {item.reason} " f"(write access requested: no)"
        for item in items
    ]


def _sectioned_markdown(
    title: str,
    sections: list[tuple[str, list[str]]],
    *,
    footer: str,
) -> str:
    lines = [f"# {title}"]
    for heading, values in sections:
        lines.extend(["", f"## {heading}"])
        lines.extend(f"- {value}" for value in values)
    lines.extend(["", footer])
    return "\n".join(lines) + "\n"
