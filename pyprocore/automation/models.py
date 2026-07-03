"""Typed models for PyProcore automation workflows."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import ConfigDict

from pyprocore.models.base import ProcoreModel


class AutomationInput(ProcoreModel):
    """Input accepted by automation workflow builders.

    Attributes:
        company_id: Optional Procore company ID used for project search.
        project_id: Optional Procore project ID. When provided, no project
            search is performed.
        project_name: Optional project name or name fragment.
        project_number: Optional Procore project number.
        item_type: Workflow target type.
        item_id: Optional Procore RFI or submittal ID.
        item_number: Optional Procore RFI or submittal number.
        download_attachments: Whether workflow builders should download files.
        output_dir: Optional directory where attachments should be saved.
    """

    company_id: int | None = None
    project_id: int | None = None
    project_name: str | None = None
    project_number: str | None = None
    item_type: Literal["rfi", "submittal"]
    item_id: int | None = None
    item_number: str | None = None
    download_attachments: bool = True
    output_dir: Path | str | None = None


class DownloadedFile(ProcoreModel):
    """A file downloaded as part of an automation workflow.

    Attributes:
        filename: Saved filename.
        path: Local filesystem path.
        source_url: Original signed Procore attachment URL, when available.
        content_type: Attachment content type, when provided by Procore.
    """

    model_config = ConfigDict(extra="allow", populate_by_name=True, arbitrary_types_allowed=True)

    filename: str
    path: Path
    source_url: str | None = None
    content_type: str | None = None


class WorkflowPackage(ProcoreModel):
    """Resolved item metadata and downloaded files for downstream automation.

    Attributes:
        item_type: Workflow target type.
        company_id: Procore company ID, when known.
        project_id: Resolved Procore project ID.
        project_name: Resolved project name, when available.
        item_id: Resolved Procore RFI or submittal ID.
        item_number: Resolved RFI or submittal number, when available.
        title: RFI subject or submittal title, when available.
        metadata: JSON-serializable typed item metadata.
        attachments: Downloaded files.
        raw: JSON-serializable raw item payload.
    """

    item_type: str
    company_id: int | None
    project_id: int
    project_name: str | None
    item_id: int
    item_number: str | None
    title: str | None
    metadata: dict[str, object]
    attachments: list[DownloadedFile]
    raw: dict[str, object]
