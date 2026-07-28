"""Local attachment manifest extraction and rendering."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable, Literal

from pyprocore.core.exceptions import ValidationError
from pyprocore.intake.models import (
    IntakeAttachmentManifest,
    IntakeAttachmentManifestItem,
    IntakeAttachmentRecord,
)
from pyprocore.intake.normalizers import attachment_values


def build_intake_attachment_manifest(
    records: Iterable[tuple[Literal["rfi", "submittal"], int, dict[str, Any]]],
) -> IntakeAttachmentManifest:
    """Build local attachment metadata without following any URLs."""
    items: list[IntakeAttachmentManifestItem] = []
    for resource, project_id, parent in records:
        for attachment in attachment_values(parent):
            url = _text(
                attachment.get("download_url")
                or attachment.get("url")
                or attachment.get("signed_url")
            )
            name = (
                _text(
                    attachment.get("filename")
                    or attachment.get("name")
                    or attachment.get("title")
                    or attachment.get("id")
                )
                or "unnamed-attachment"
            )
            normalized = IntakeAttachmentRecord(
                source_resource=resource,
                project_id=project_id,
                parent_id=_text(parent.get("id")),
                parent_number=_text(parent.get("number")),
                id=_text(attachment.get("id")),
                name=name,
                url=url,
                content_type=_text(attachment.get("content_type") or attachment.get("mime_type")),
                size=_integer(attachment.get("size") or attachment.get("file_size")),
            )
            items.append(
                IntakeAttachmentManifestItem(
                    attachment=normalized,
                    download_available=bool(url),
                    note=(
                        "Candidate URL present; user-run downloads still depend on DMSA "
                        "permissions and URL validity."
                        if url
                        else "No download URL was present in the supplied local payload."
                    ),
                )
            )
    return IntakeAttachmentManifest(generated_at=datetime.now(UTC), items=items)


def render_attachment_manifest_json(manifest: IntakeAttachmentManifest) -> str:
    """Render an attachment manifest as JSON."""
    return json.dumps(manifest.model_dump(mode="json"), indent=2, sort_keys=True)


def render_attachment_manifest_markdown(manifest: IntakeAttachmentManifest) -> str:
    """Render an attachment manifest as Markdown."""
    lines = [
        "# Intake Attachment Manifest",
        "",
        manifest.note,
        "",
        "| Resource | Project | Parent | File | URL present |",
        "| --- | ---: | --- | --- | --- |",
    ]
    for item in manifest.items:
        attachment = item.attachment
        lines.append(
            f"| {attachment.source_resource} | {attachment.project_id} | "
            f"{attachment.parent_number or attachment.parent_id or '-'} | "
            f"{attachment.name} | {'yes' if item.download_available else 'no'} |"
        )
    if not manifest.items:
        lines.append("| - | - | - | No attachment metadata found | no |")
    return "\n".join(lines) + "\n"


def write_attachment_manifest(
    manifest: IntakeAttachmentManifest,
    path: str | Path,
    *,
    output_root: str | Path | None = None,
    overwrite: bool = False,
) -> Path:
    """Write a JSON or Markdown manifest inside an optional output root."""
    destination = _safe_destination(path, output_root)
    if destination.suffix.casefold() not in {".json", ".md"}:
        raise ValidationError("Attachment manifests must use .json or .md.")
    if destination.exists() and not overwrite:
        raise ValidationError(f"Refusing to overwrite attachment manifest: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    content = (
        render_attachment_manifest_json(manifest)
        if destination.suffix.casefold() == ".json"
        else render_attachment_manifest_markdown(manifest)
    )
    destination.write_text(content.rstrip() + "\n", encoding="utf-8")
    return destination


def _safe_destination(path: str | Path, output_root: str | Path | None) -> Path:
    candidate = Path(path).expanduser()
    if ".." in candidate.parts:
        raise ValidationError("Path traversal is not allowed for intake manifests.")
    destination = candidate.resolve()
    if output_root is not None:
        root = Path(output_root).expanduser().resolve()
        if not destination.is_relative_to(root):
            raise ValidationError("Intake manifest path must remain inside output_dir.")
    return destination


def _text(value: Any) -> str | None:
    return None if value in (None, "") else str(value)


def _integer(value: Any) -> int | None:
    try:
        return None if value in (None, "") else int(value)
    except (TypeError, ValueError):
        return None
