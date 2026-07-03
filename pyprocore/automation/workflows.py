"""High-level automation workflow package builders."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from pyprocore.automation.models import AutomationInput, DownloadedFile, WorkflowPackage
from pyprocore.automation.resolver import resolve_project, resolve_rfi, resolve_submittal
from pyprocore.core.exceptions import ValidationError
from pyprocore.models import RFI, Submittal
from pyprocore.services.files import DEFAULT_DOWNLOAD_DIR, FileDownloadService
from pyprocore.services.rfis import get_rfi
from pyprocore.services.submittals import get_submittal


def build_workflow_package(input_data: AutomationInput) -> WorkflowPackage:
    """Build a resolved workflow package for an RFI or submittal.

    Args:
        input_data: Automation workflow input.

    Returns:
        A workflow package containing item metadata and downloaded files.

    Raises:
        ValidationError: If the workflow type is unsupported or required
            project/item identifiers are missing.
    """
    project = resolve_project(input_data)

    if input_data.item_type == "rfi":
        resolved_rfi = resolve_rfi(input_data, project.id)
        rfi = (
            resolved_rfi if input_data.item_id is not None else get_rfi(project.id, resolved_rfi.id)
        )
        return _build_rfi_package(input_data, project.id, project.name, rfi)

    if input_data.item_type == "submittal":
        resolved_submittal = resolve_submittal(input_data, project.id)
        submittal = (
            resolved_submittal
            if input_data.item_id is not None
            else get_submittal(project.id, resolved_submittal.id)
        )
        return _build_submittal_package(input_data, project.id, project.name, submittal)

    raise ValidationError(f"Unsupported automation item_type: {input_data.item_type!r}.")


def build_rfi_package(
    *,
    company_id: int | None = None,
    project_id: int | None = None,
    project_name: str | None = None,
    project_number: str | None = None,
    rfi_id: int | None = None,
    number: str | None = None,
    download_attachments: bool = True,
    output_dir: Path | str | None = None,
) -> WorkflowPackage:
    """Build a workflow package for one RFI.

    Args:
        company_id: Optional company ID used for project search.
        project_id: Optional project ID.
        project_name: Optional project name or name fragment.
        project_number: Optional project number.
        rfi_id: Optional RFI ID.
        number: Optional RFI number.
        download_attachments: Whether to download RFI attachments.
        output_dir: Optional attachment output directory.

    Returns:
        A workflow package for the resolved RFI.
    """
    return build_workflow_package(
        AutomationInput(
            company_id=company_id,
            project_id=project_id,
            project_name=project_name,
            project_number=project_number,
            item_type="rfi",
            item_id=rfi_id,
            item_number=number,
            download_attachments=download_attachments,
            output_dir=output_dir,
        )
    )


def build_submittal_package(
    *,
    company_id: int | None = None,
    project_id: int | None = None,
    project_name: str | None = None,
    project_number: str | None = None,
    submittal_id: int | None = None,
    number: str | None = None,
    download_attachments: bool = True,
    output_dir: Path | str | None = None,
) -> WorkflowPackage:
    """Build a workflow package for one submittal.

    Args:
        company_id: Optional company ID used for project search.
        project_id: Optional project ID.
        project_name: Optional project name or name fragment.
        project_number: Optional project number.
        submittal_id: Optional submittal ID.
        number: Optional submittal number.
        download_attachments: Whether to download submittal attachments.
        output_dir: Optional attachment output directory.

    Returns:
        A workflow package for the resolved submittal.
    """
    return build_workflow_package(
        AutomationInput(
            company_id=company_id,
            project_id=project_id,
            project_name=project_name,
            project_number=project_number,
            item_type="submittal",
            item_id=submittal_id,
            item_number=number,
            download_attachments=download_attachments,
            output_dir=output_dir,
        )
    )


def _build_rfi_package(
    input_data: AutomationInput,
    project_id: int,
    project_name: str | None,
    rfi: RFI,
) -> WorkflowPackage:
    """Build a workflow package from resolved RFI metadata."""
    raw = rfi.model_dump(mode="json")
    attachments = _extract_rfi_attachments(raw)
    package_slug = _workflow_slug("rfi", rfi.number, rfi.id)
    downloaded_files = _download_attachments(
        attachments=attachments,
        input_data=input_data,
        fallback_prefix=package_slug,
    )

    return WorkflowPackage(
        item_type="rfi",
        company_id=input_data.company_id,
        project_id=project_id,
        project_name=project_name,
        item_id=rfi.id,
        item_number=_string_or_none(rfi.number),
        title=_rfi_title(rfi),
        metadata=raw,
        attachments=downloaded_files,
        raw=raw,
    )


def _build_submittal_package(
    input_data: AutomationInput,
    project_id: int,
    project_name: str | None,
    submittal: Submittal,
) -> WorkflowPackage:
    """Build a workflow package from resolved submittal metadata."""
    raw = submittal.model_dump(mode="json")
    attachments = _extract_submittal_attachments(raw)
    package_slug = _workflow_slug("submittal", submittal.number, submittal.id)
    downloaded_files = _download_attachments(
        attachments=attachments,
        input_data=input_data,
        fallback_prefix=package_slug,
    )

    return WorkflowPackage(
        item_type="submittal",
        company_id=input_data.company_id,
        project_id=project_id,
        project_name=project_name,
        item_id=submittal.id,
        item_number=_string_or_none(submittal.number),
        title=submittal.title,
        metadata=raw,
        attachments=downloaded_files,
        raw=raw,
    )


def _download_attachments(
    *,
    attachments: Iterable[Mapping[str, Any]],
    input_data: AutomationInput,
    fallback_prefix: str,
) -> list[DownloadedFile]:
    """Download attachment mappings and return workflow file models."""
    if not input_data.download_attachments:
        return []

    output_dir = _output_dir(input_data, fallback_prefix)
    file_service = FileDownloadService()
    downloaded_files: list[DownloadedFile] = []

    for index, attachment in enumerate(attachments, start=1):
        saved_path = file_service.download_attachment(
            attachment,
            output_dir,
            fallback_name=f"{fallback_prefix}-{index}",
        )
        if saved_path is None:
            continue

        downloaded_files.append(
            DownloadedFile(
                filename=saved_path.name,
                path=saved_path,
                source_url=_string_or_none(attachment.get("url")),
                content_type=_string_or_none(attachment.get("content_type")),
            )
        )

    return downloaded_files


def _output_dir(input_data: AutomationInput, fallback_prefix: str) -> Path:
    """Return the workflow attachment output directory."""
    if input_data.output_dir is not None:
        return Path(input_data.output_dir)
    return DEFAULT_DOWNLOAD_DIR / fallback_prefix


def _workflow_slug(item_type: str, number: object | None, item_id: int) -> str:
    """Return the default directory/fallback prefix for a workflow item."""
    identifier = _string_or_none(number) or str(item_id)
    safe_identifier = "".join(
        character if character.isalnum() or character in {"_", "-"} else "_"
        for character in identifier
    ).strip("_-")
    return f"{item_type}_{safe_identifier or item_id}"


def _extract_rfi_attachments(rfi: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Extract ``questions[].attachments[]`` mappings from an RFI payload."""
    attachments: list[dict[str, Any]] = []
    questions = rfi.get("questions", [])
    if not isinstance(questions, list):
        return attachments

    for question in questions:
        if not isinstance(question, Mapping):
            continue
        question_attachments = question.get("attachments", [])
        if not isinstance(question_attachments, list):
            continue
        attachments.extend(
            dict(attachment)
            for attachment in question_attachments
            if isinstance(attachment, Mapping)
        )

    return attachments


def _extract_submittal_attachments(submittal: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Extract ``attachments[]`` mappings from a submittal payload."""
    attachments = submittal.get("attachments", [])
    if not isinstance(attachments, list):
        return []
    return [dict(attachment) for attachment in attachments if isinstance(attachment, Mapping)]


def _rfi_title(rfi: RFI) -> str | None:
    """Return the best available title for an RFI."""
    explicit_title = getattr(rfi, "title", None)
    if isinstance(explicit_title, str) and explicit_title.strip():
        return explicit_title
    return rfi.subject


def _string_or_none(value: object | None) -> str | None:
    """Return a string representation when a value is present."""
    return None if value is None else str(value)
