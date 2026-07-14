"""CSV and JSONL export helpers for Procore workflow automation."""

from __future__ import annotations

import csv
import json
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any

from pyprocore.models import RFI, Correspondence, Document, Observation, PunchItem, Submittal
from pyprocore.services.correspondence import list_correspondences
from pyprocore.services.observations import list_observations
from pyprocore.services.punch_items import list_punch_items
from pyprocore.services.rfis import list_rfis
from pyprocore.services.submittals import list_submittals
from pyprocore.workflows.utils import (
    attachment_count,
    get_value,
    item_title,
    model_to_dict,
    scalar_text,
)

RFI_CSV_HEADERS = [
    "id",
    "number",
    "subject",
    "status",
    "created_at",
    "updated_at",
    "due_date",
    "ball_in_court",
    "responsible_contractor",
    "assignee",
    "question_count",
    "attachment_count",
]

SUBMITTAL_CSV_HEADERS = [
    "id",
    "number",
    "title",
    "status",
    "created_at",
    "updated_at",
    "due_date",
    "ball_in_court",
    "responsible_contractor",
    "attachment_count",
]

DOCUMENT_CSV_HEADERS = [
    "id",
    "name",
    "filename",
    "folder_id",
    "content_type",
    "file_size",
    "created_at",
    "updated_at",
    "download_url",
]

OBSERVATION_CSV_HEADERS = [
    "id",
    "number",
    "title",
    "status",
    "type",
    "priority",
    "created_at",
    "updated_at",
    "due_date",
    "assignee",
    "created_by",
    "attachment_count",
]

PUNCH_ITEM_CSV_HEADERS = [
    "id",
    "number",
    "title",
    "status",
    "type",
    "priority",
    "created_at",
    "updated_at",
    "due_date",
    "assignee",
    "created_by",
    "attachment_count",
]

CORRESPONDENCE_CSV_HEADERS = [
    "id",
    "number",
    "subject",
    "title",
    "status",
    "generic_tool_id",
    "created_at",
    "updated_at",
    "due_date",
    "assignee",
    "created_by",
    "attachment_count",
]


def export_rfis_to_csv(
    project_id: int,
    output_path: Path | str,
    *,
    status: str | None = None,
    updated_after: str | None = None,
    updated_before: str | None = None,
    created_after: str | None = None,
    created_before: str | None = None,
    params: Mapping[str, Any] | None = None,
    **extra_params: Any,
) -> Path:
    """Export project RFIs to a CSV file.

    Args:
        project_id: Procore project ID.
        output_path: CSV path to create.
        status: Optional status filter.
        updated_after: Optional lower bound for updated date filtering.
        updated_before: Optional upper bound for updated date filtering.
        created_after: Optional lower bound for created date filtering.
        created_before: Optional upper bound for created date filtering.
        params: Additional query parameters passed to the RFI service.
        **extra_params: Additional Procore query parameters.

    Returns:
        The created CSV path.
    """
    rfis = _load_rfis(
        project_id,
        status=status,
        updated_after=updated_after,
        updated_before=updated_before,
        created_after=created_after,
        created_before=created_before,
        params=params,
        **extra_params,
    )
    return write_rfis_csv(rfis, output_path)


def export_submittals_to_csv(
    project_id: int,
    output_path: Path | str,
    *,
    status: str | None = None,
    updated_after: str | None = None,
    updated_before: str | None = None,
    created_after: str | None = None,
    created_before: str | None = None,
    params: Mapping[str, Any] | None = None,
    **extra_params: Any,
) -> Path:
    """Export project submittals to a CSV file.

    Args:
        project_id: Procore project ID.
        output_path: CSV path to create.
        status: Optional status filter.
        updated_after: Optional lower bound for updated date filtering.
        updated_before: Optional upper bound for updated date filtering.
        created_after: Optional lower bound for created date filtering.
        created_before: Optional upper bound for created date filtering.
        params: Additional query parameters passed to the submittal service.
        **extra_params: Additional Procore query parameters.

    Returns:
        The created CSV path.
    """
    submittals = _load_submittals(
        project_id,
        status=status,
        updated_after=updated_after,
        updated_before=updated_before,
        created_after=created_after,
        created_before=created_before,
        params=params,
        **extra_params,
    )
    return write_submittals_csv(submittals, output_path)


def export_rfis_to_jsonl(
    project_id: int,
    output_path: Path | str,
    *,
    status: str | None = None,
    updated_after: str | None = None,
    updated_before: str | None = None,
    created_after: str | None = None,
    created_before: str | None = None,
    params: Mapping[str, Any] | None = None,
    **extra_params: Any,
) -> Path:
    """Export project RFIs to newline-delimited JSON.

    Args:
        project_id: Procore project ID.
        output_path: JSONL path to create.
        status: Optional status filter.
        updated_after: Optional lower bound for updated date filtering.
        updated_before: Optional upper bound for updated date filtering.
        created_after: Optional lower bound for created date filtering.
        created_before: Optional upper bound for created date filtering.
        params: Additional query parameters passed to the RFI service.
        **extra_params: Additional Procore query parameters.

    Returns:
        The created JSONL path.
    """
    rfis = _load_rfis(
        project_id,
        status=status,
        updated_after=updated_after,
        updated_before=updated_before,
        created_after=created_after,
        created_before=created_before,
        params=params,
        **extra_params,
    )
    return _write_jsonl(rfis, output_path)


def export_submittals_to_jsonl(
    project_id: int,
    output_path: Path | str,
    *,
    status: str | None = None,
    updated_after: str | None = None,
    updated_before: str | None = None,
    created_after: str | None = None,
    created_before: str | None = None,
    params: Mapping[str, Any] | None = None,
    **extra_params: Any,
) -> Path:
    """Export project submittals to newline-delimited JSON.

    Args:
        project_id: Procore project ID.
        output_path: JSONL path to create.
        status: Optional status filter.
        updated_after: Optional lower bound for updated date filtering.
        updated_before: Optional upper bound for updated date filtering.
        created_after: Optional lower bound for created date filtering.
        created_before: Optional upper bound for created date filtering.
        params: Additional query parameters passed to the submittal service.
        **extra_params: Additional Procore query parameters.

    Returns:
        The created JSONL path.
    """
    submittals = _load_submittals(
        project_id,
        status=status,
        updated_after=updated_after,
        updated_before=updated_before,
        created_after=created_after,
        created_before=created_before,
        params=params,
        **extra_params,
    )
    return _write_jsonl(submittals, output_path)


def export_observations_to_csv(
    company_id: int | None,
    project_id: int,
    output_path: Path | str,
    **filters: Any,
) -> Path:
    """Export project observations to a CSV file."""
    observations = list_observations(company_id, project_id, **filters)
    return write_observations_csv(observations, output_path)


def export_observations_to_jsonl(
    company_id: int | None,
    project_id: int,
    output_path: Path | str,
    **filters: Any,
) -> Path:
    """Export project observations to newline-delimited JSON."""
    observations = list_observations(company_id, project_id, **filters)
    return _write_jsonl(observations, output_path)


def export_punch_items_to_csv(
    company_id: int | None,
    project_id: int,
    output_path: Path | str,
    **filters: Any,
) -> Path:
    """Export project punch items to a CSV file."""
    punch_items = list_punch_items(company_id, project_id, **filters)
    return write_punch_items_csv(punch_items, output_path)


def export_punch_items_to_jsonl(
    company_id: int | None,
    project_id: int,
    output_path: Path | str,
    **filters: Any,
) -> Path:
    """Export project punch items to newline-delimited JSON."""
    punch_items = list_punch_items(company_id, project_id, **filters)
    return _write_jsonl(punch_items, output_path)


def export_correspondences_to_csv(
    company_id: int | None,
    project_id: int,
    generic_tool_id: int,
    output_path: Path | str,
    **filters: Any,
) -> Path:
    """Export Generic Tool correspondence items to a CSV file."""
    correspondences = list_correspondences(company_id, project_id, generic_tool_id, **filters)
    return write_correspondences_csv(correspondences, output_path)


def export_correspondences_to_jsonl(
    company_id: int | None,
    project_id: int,
    generic_tool_id: int,
    output_path: Path | str,
    **filters: Any,
) -> Path:
    """Export Generic Tool correspondence items to newline-delimited JSON."""
    correspondences = list_correspondences(company_id, project_id, generic_tool_id, **filters)
    return _write_jsonl(correspondences, output_path)


def write_rfis_csv(rfis: Sequence[RFI], output_path: Path | str) -> Path:
    """Write already-loaded RFIs to a CSV file."""
    return _write_csv(rfis, output_path, RFI_CSV_HEADERS, _rfi_row)


def write_submittals_csv(submittals: Sequence[Submittal], output_path: Path | str) -> Path:
    """Write already-loaded submittals to a CSV file."""
    return _write_csv(submittals, output_path, SUBMITTAL_CSV_HEADERS, _submittal_row)


def write_documents_csv(documents: Sequence[Document], output_path: Path | str) -> Path:
    """Write already-loaded documents to a CSV file."""
    return _write_csv(documents, output_path, DOCUMENT_CSV_HEADERS, _document_row)


def write_observations_csv(observations: Sequence[Observation], output_path: Path | str) -> Path:
    """Write already-loaded observations to a CSV file."""
    return _write_csv(observations, output_path, OBSERVATION_CSV_HEADERS, _observation_row)


def write_punch_items_csv(punch_items: Sequence[PunchItem], output_path: Path | str) -> Path:
    """Write already-loaded punch items to a CSV file."""
    return _write_csv(punch_items, output_path, PUNCH_ITEM_CSV_HEADERS, _punch_item_row)


def write_correspondences_csv(
    correspondences: Sequence[Correspondence],
    output_path: Path | str,
) -> Path:
    """Write already-loaded correspondences to a CSV file."""
    return _write_csv(
        correspondences,
        output_path,
        CORRESPONDENCE_CSV_HEADERS,
        _correspondence_row,
    )


def _load_rfis(
    project_id: int,
    *,
    status: str | None,
    updated_after: str | None,
    updated_before: str | None,
    created_after: str | None,
    created_before: str | None,
    params: Mapping[str, Any] | None,
    **extra_params: Any,
) -> list[RFI]:
    """Load RFIs using the existing service layer."""
    return list_rfis(
        project_id,
        status=status,
        updated_after=updated_after,
        updated_before=updated_before,
        created_after=created_after,
        created_before=created_before,
        params=params,
        **extra_params,
    )


def _load_submittals(
    project_id: int,
    *,
    status: str | None,
    updated_after: str | None,
    updated_before: str | None,
    created_after: str | None,
    created_before: str | None,
    params: Mapping[str, Any] | None,
    **extra_params: Any,
) -> list[Submittal]:
    """Load submittals using the existing service layer."""
    return list_submittals(
        project_id,
        status=status,
        updated_after=updated_after,
        updated_before=updated_before,
        created_after=created_after,
        created_before=created_before,
        params=params,
        **extra_params,
    )


def _write_csv(
    items: Sequence[object],
    output_path: Path | str,
    headers: list[str],
    row_builder: Callable[[object], dict[str, object]],
) -> Path:
    """Write workflow items to CSV and return the saved path."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", newline="", encoding="utf-8") as file_handle:
        writer = csv.DictWriter(file_handle, fieldnames=headers)
        writer.writeheader()
        for item in items:
            writer.writerow(row_builder(item))

    return path


def _write_jsonl(items: Sequence[object], output_path: Path | str) -> Path:
    """Write workflow items to newline-delimited JSON and return the path."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as file_handle:
        for item in items:
            file_handle.write(json.dumps(model_to_dict(item), default=str, sort_keys=True))
            file_handle.write("\n")

    return path


def _rfi_row(rfi: object) -> dict[str, object]:
    """Convert one RFI model into a CSV row."""
    questions = get_value(rfi, "questions") or []
    question_count = len(questions) if isinstance(questions, Sequence) else 0
    return {
        "id": scalar_text(get_value(rfi, "id")),
        "number": scalar_text(get_value(rfi, "number")),
        "subject": item_title(rfi),
        "status": scalar_text(get_value(rfi, "status")),
        "created_at": scalar_text(get_value(rfi, "created_at")),
        "updated_at": scalar_text(get_value(rfi, "updated_at")),
        "due_date": scalar_text(get_value(rfi, "due_date")),
        "ball_in_court": scalar_text(get_value(rfi, "ball_in_court")),
        "responsible_contractor": scalar_text(get_value(rfi, "responsible_contractor")),
        "assignee": scalar_text(get_value(rfi, "assignee")),
        "question_count": question_count,
        "attachment_count": attachment_count(rfi, item_type="rfi"),
    }


def _submittal_row(submittal: object) -> dict[str, object]:
    """Convert one submittal model into a CSV row."""
    return {
        "id": scalar_text(get_value(submittal, "id")),
        "number": scalar_text(get_value(submittal, "number")),
        "title": item_title(submittal),
        "status": scalar_text(get_value(submittal, "status")),
        "created_at": scalar_text(get_value(submittal, "created_at")),
        "updated_at": scalar_text(get_value(submittal, "updated_at")),
        "due_date": scalar_text(get_value(submittal, "due_date")),
        "ball_in_court": scalar_text(get_value(submittal, "ball_in_court")),
        "responsible_contractor": scalar_text(get_value(submittal, "responsible_contractor")),
        "attachment_count": attachment_count(submittal, item_type="submittal"),
    }


def _document_row(document: object) -> dict[str, object]:
    """Convert one document model into a CSV row."""
    return {
        "id": scalar_text(get_value(document, "id")),
        "name": scalar_text(get_value(document, "name")),
        "filename": scalar_text(get_value(document, "filename", "file_name")),
        "folder_id": scalar_text(get_value(document, "folder_id")),
        "content_type": scalar_text(get_value(document, "content_type")),
        "file_size": scalar_text(get_value(document, "file_size")),
        "created_at": scalar_text(get_value(document, "created_at")),
        "updated_at": scalar_text(get_value(document, "updated_at")),
        "download_url": scalar_text(get_value(document, "download_url", "url")),
    }


def _observation_row(observation: object) -> dict[str, object]:
    """Convert one observation model into a CSV row."""
    return {
        "id": scalar_text(get_value(observation, "id")),
        "number": scalar_text(get_value(observation, "number")),
        "title": item_title(observation),
        "status": scalar_text(get_value(observation, "status")),
        "type": scalar_text(get_value(observation, "type", "observation_type")),
        "priority": scalar_text(get_value(observation, "priority")),
        "created_at": scalar_text(get_value(observation, "created_at")),
        "updated_at": scalar_text(get_value(observation, "updated_at")),
        "due_date": scalar_text(get_value(observation, "due_date")),
        "assignee": scalar_text(get_value(observation, "assignee")),
        "created_by": scalar_text(get_value(observation, "created_by")),
        "attachment_count": attachment_count(observation, item_type="observation"),
    }


def _punch_item_row(punch_item: object) -> dict[str, object]:
    """Convert one punch item model into a CSV row."""
    return {
        "id": scalar_text(get_value(punch_item, "id")),
        "number": scalar_text(get_value(punch_item, "number")),
        "title": item_title(punch_item),
        "status": scalar_text(get_value(punch_item, "status")),
        "type": scalar_text(get_value(punch_item, "type")),
        "priority": scalar_text(get_value(punch_item, "priority")),
        "created_at": scalar_text(get_value(punch_item, "created_at")),
        "updated_at": scalar_text(get_value(punch_item, "updated_at")),
        "due_date": scalar_text(get_value(punch_item, "due_date")),
        "assignee": scalar_text(get_value(punch_item, "assignee", "assigned_to")),
        "created_by": scalar_text(get_value(punch_item, "created_by")),
        "attachment_count": attachment_count(punch_item, item_type="punch_item"),
    }


def _correspondence_row(correspondence: object) -> dict[str, object]:
    """Convert one correspondence model into a CSV row."""
    return {
        "id": scalar_text(get_value(correspondence, "id")),
        "number": scalar_text(get_value(correspondence, "number")),
        "subject": scalar_text(get_value(correspondence, "subject")),
        "title": item_title(correspondence),
        "status": scalar_text(get_value(correspondence, "status")),
        "generic_tool_id": scalar_text(get_value(correspondence, "generic_tool_id")),
        "created_at": scalar_text(get_value(correspondence, "created_at")),
        "updated_at": scalar_text(get_value(correspondence, "updated_at")),
        "due_date": scalar_text(get_value(correspondence, "due_date")),
        "assignee": scalar_text(get_value(correspondence, "assignee")),
        "created_by": scalar_text(get_value(correspondence, "created_by")),
        "attachment_count": attachment_count(correspondence, item_type="correspondence"),
    }
