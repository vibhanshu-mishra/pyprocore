"""Typed Pydantic models for common Procore resources."""

from __future__ import annotations

from typing import Any

from pydantic import Field, HttpUrl

from pyprocore.models.base import ProcoreModel


class Status(ProcoreModel):
    """Status metadata returned by Procore resources."""

    id: int | None = None
    name: str | None = None
    status: str | None = None


class User(ProcoreModel):
    """Procore user summary."""

    id: int | None = None
    name: str | None = None
    login: str | None = None
    email_address: str | None = None


class Attachment(ProcoreModel):
    """Attachment metadata with a signed download URL."""

    id: int | None = None
    name: str | None = None
    filename: str | None = None
    file_name: str | None = None
    url: str | HttpUrl | None = None
    content_type: str | None = None


class Company(ProcoreModel):
    """Procore company resource."""

    id: int
    name: str | None = None


class Project(ProcoreModel):
    """Procore project resource."""

    id: int
    name: str | None = None
    project_number: str | None = None
    active: bool | None = None
    company: Company | None = None


class RFIQuestion(ProcoreModel):
    """Question nested under a Procore RFI."""

    id: int | None = None
    body: str | None = None
    plain_text_body: str | None = None
    attachments: list[Attachment] = Field(default_factory=list)


class RFI(ProcoreModel):
    """Procore RFI resource."""

    id: int
    number: str | int | None = None
    subject: str | None = None
    status: Status | str | None = None
    assignee: User | None = None
    created_by: User | None = None
    questions: list[RFIQuestion] = Field(default_factory=list)


class Submittal(ProcoreModel):
    """Procore submittal resource."""

    id: int
    number: str | int | None = None
    title: str | None = None
    status: Status | str | None = None
    responsible_contractor: dict[str, Any] | None = None
    attachments: list[Attachment] = Field(default_factory=list)


class Observation(ProcoreModel):
    """Flexible Procore observation item resource."""

    id: int | None = None
    number: str | int | None = None
    title: str | None = None
    name: str | None = None
    description: str | None = None
    status: Status | str | None = None
    type: str | None = None
    observation_type: str | dict[str, Any] | None = None
    priority: str | Status | None = None
    assignee: User | dict[str, Any] | None = None
    created_by: User | dict[str, Any] | None = None
    due_date: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    attachments: list[Attachment] = Field(default_factory=list)


class PunchItem(ProcoreModel):
    """Flexible Procore punch item resource."""

    id: int | None = None
    number: str | int | None = None
    title: str | None = None
    name: str | None = None
    description: str | None = None
    status: Status | str | None = None
    type: str | None = None
    priority: str | Status | None = None
    assignee: User | dict[str, Any] | None = None
    assigned_to: User | dict[str, Any] | None = None
    created_by: User | dict[str, Any] | None = None
    due_date: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    attachments: list[Attachment] = Field(default_factory=list)


class GenericTool(ProcoreModel):
    """Flexible Procore Generic Tool metadata resource."""

    id: int | None = None
    name: str | None = None
    title: str | None = None
    tool_type: str | None = None
    type: str | None = None
    slug: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class Correspondence(ProcoreModel):
    """Flexible Procore correspondence or Generic Tool Item resource."""

    id: int | None = None
    number: str | int | None = None
    subject: str | None = None
    title: str | None = None
    name: str | None = None
    description: str | None = None
    status: Status | str | None = None
    generic_tool_id: int | None = None
    generic_tool: GenericTool | dict[str, Any] | None = None
    assignee: User | dict[str, Any] | None = None
    created_by: User | dict[str, Any] | None = None
    due_date: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    attachments: list[Attachment] = Field(default_factory=list)


class Meeting(ProcoreModel):
    """Flexible Procore meeting resource."""

    id: int | None = None
    number: str | int | None = None
    title: str | None = None
    name: str | None = None
    description: str | None = None
    status: Status | str | None = None
    meeting_date: str | None = None
    date: str | None = None
    start_time: str | None = None
    end_time: str | None = None
    location: str | dict[str, Any] | None = None
    created_by: User | dict[str, Any] | None = None
    created_at: str | None = None
    updated_at: str | None = None
    attachments: list[Attachment] = Field(default_factory=list)


class InspectionItem(ProcoreModel):
    """Flexible inspection checklist item resource."""

    id: int | None = None
    number: str | int | None = None
    title: str | None = None
    name: str | None = None
    description: str | None = None
    status: Status | str | None = None
    response: str | dict[str, Any] | None = None
    comments: str | None = None
    attachments: list[Attachment] = Field(default_factory=list)


class Inspection(ProcoreModel):
    """Flexible Procore inspection/checklist resource.

    Some Procore APIs expose inspections through checklist/checklists
    terminology. PyProcore keeps the public model name user-friendly while
    preserving unknown checklist payload fields.
    """

    id: int | None = None
    number: str | int | None = None
    title: str | None = None
    name: str | None = None
    description: str | None = None
    status: Status | str | None = None
    type: str | dict[str, Any] | None = None
    inspection_type: str | dict[str, Any] | None = None
    checklist_type: str | dict[str, Any] | None = None
    assignee: User | dict[str, Any] | None = None
    created_by: User | dict[str, Any] | None = None
    due_date: str | None = None
    performed_on: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    items: list[InspectionItem] = Field(default_factory=list)
    checklist_items: list[InspectionItem] = Field(default_factory=list)
    attachments: list[Attachment] = Field(default_factory=list)


class Incident(ProcoreModel):
    """Flexible Procore incident resource."""

    id: int | None = None
    number: str | int | None = None
    title: str | None = None
    name: str | None = None
    description: str | None = None
    status: Status | str | None = None
    type: str | dict[str, Any] | None = None
    incident_type: str | dict[str, Any] | None = None
    severity: str | Status | None = None
    location: str | dict[str, Any] | None = None
    occurred_at: str | None = None
    incident_date: str | None = None
    reported_by: User | dict[str, Any] | None = None
    created_by: User | dict[str, Any] | None = None
    created_at: str | None = None
    updated_at: str | None = None
    attachments: list[Attachment] = Field(default_factory=list)


class IncidentConfiguration(ProcoreModel):
    """Flexible Procore project incident configuration resource."""

    id: int | None = None
    project_id: int | None = None
    enabled: bool | None = None
    incident_types: list[dict[str, Any]] = Field(default_factory=list)
    statuses: list[dict[str, Any]] = Field(default_factory=list)
    severity_levels: list[dict[str, Any]] = Field(default_factory=list)
    created_at: str | None = None
    updated_at: str | None = None


class DocumentFolder(ProcoreModel):
    """Procore document folder resource."""

    id: int | None = None
    name: str | None = None
    type: str | None = None
    item_type: str | None = None
    parent_id: int | None = None
    path: str | None = None
    folders: list["DocumentFolder"] = Field(default_factory=list)
    files: list["Document"] = Field(default_factory=list)
    created_at: str | None = None
    updated_at: str | None = None


class Document(ProcoreModel):
    """Procore document resource."""

    id: int | None = None
    name: str | None = None
    type: str | None = None
    item_type: str | None = None
    filename: str | None = None
    file_name: str | None = None
    url: str | HttpUrl | None = None
    download_url: str | HttpUrl | None = None
    folder_id: int | None = None
    content_type: str | None = None
    file_size: int | None = None
    created_at: str | None = None
    updated_at: str | None = None


class DrawingArea(ProcoreModel):
    """Procore drawing area resource."""

    id: int | None = None
    name: str | None = None
    position: int | None = None
    created_at: str | None = None
    updated_at: str | None = None


class DrawingDiscipline(ProcoreModel):
    """Procore drawing discipline resource."""

    id: int | None = None
    name: str | None = None
    abbreviation: str | None = None
    position: int | None = None


class Drawing(ProcoreModel):
    """Procore drawing resource."""

    id: int | None = None
    number: str | int | None = None
    title: str | None = None
    name: str | None = None
    filename: str | None = None
    file_name: str | None = None
    discipline: str | DrawingDiscipline | None = None
    discipline_id: int | None = None
    drawing_area: DrawingArea | str | None = None
    drawing_area_id: int | None = None
    revision_number: str | int | None = None
    current_revision_id: int | None = None
    status: str | Status | None = None
    issued_date: str | None = None
    received_date: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    url: str | HttpUrl | None = None
    download_url: str | HttpUrl | None = None


class PhotoAlbum(ProcoreModel):
    """Procore photo album resource.

    Procore calls photo albums ``image_categories`` in the REST API.
    """

    id: int | None = None
    name: str | None = None
    description: str | None = None
    image_count: int | None = None
    photos_count: int | None = None
    created_at: str | None = None
    updated_at: str | None = None


class PhotoImage(ProcoreModel):
    """Procore photo/image resource."""

    id: int | None = None
    name: str | None = None
    filename: str | None = None
    file_name: str | None = None
    image_name: str | None = None
    original_filename: str | None = None
    description: str | None = None
    image_category_id: int | None = None
    private: bool | None = None
    starred: bool | None = None
    taken_at: str | None = None
    exposure_date: str | None = None
    log_date: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    thumbnail_url: str | HttpUrl | None = None
    url: str | HttpUrl | None = None
    download_url: str | HttpUrl | None = None
    file_url: str | HttpUrl | None = None
    original_url: str | HttpUrl | None = None
    full_size_url: str | HttpUrl | None = None


class PhotoAlbumDownloadResult(ProcoreModel):
    """Summary returned after downloading a photo album."""

    album_id: int
    requested: int
    downloaded_files: list[str] = Field(default_factory=list)
    skipped: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


class DailyLogCount(ProcoreModel):
    """Procore Daily Log count resource."""

    log_type: str | None = None
    type: str | None = None
    name: str | None = None
    count: int | None = None


class DailyLogHeader(ProcoreModel):
    """Procore Daily Log header resource."""

    id: int | None = None
    log_date: str | None = None
    date: str | None = None
    status: str | Status | None = None
    created_at: str | None = None
    updated_at: str | None = None


class DailyLogEntry(ProcoreModel):
    """Flexible Procore Daily Log entry resource."""

    id: int | None = None
    log_type: str | None = None
    log_date: str | None = None
    date: str | None = None
    comments: str | None = None
    description: str | None = None
    notes: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class DelayLogType(ProcoreModel):
    """Procore delay log type resource."""

    id: int | None = None
    name: str | None = None
    description: str | None = None


class DailyLogsByType(ProcoreModel):
    """Daily Log entries grouped by log type for one date."""

    project_id: int
    log_date: str | None = None
    logs: dict[str, list[DailyLogEntry]] = Field(default_factory=dict)
    errors: dict[str, str] = Field(default_factory=dict)


class SpecificationSet(ProcoreModel):
    """Procore specification set resource."""

    id: int | None = None
    name: str | None = None
    description: str | None = None
    issue_date: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class SpecificationSection(ProcoreModel):
    """Procore specification section resource."""

    id: int | None = None
    number: str | int | None = None
    title: str | None = None
    description: str | None = None
    specification_set_id: int | None = None
    specification_area_id: int | None = None
    division_id: int | None = None
    current_revision_id: int | None = None
    created_at: str | None = None
    updated_at: str | None = None


class SpecificationSectionRevision(ProcoreModel):
    """Procore specification section revision resource."""

    id: int | None = None
    number: str | int | None = None
    title: str | None = None
    description: str | None = None
    revision_number: str | int | None = None
    specification_section_id: int | None = None
    specification_set_id: int | None = None
    specification_area_id: int | None = None
    division_id: int | None = None
    filename: str | None = None
    file_name: str | None = None
    url: str | HttpUrl | None = None
    download_url: str | HttpUrl | None = None
    file_url: str | HttpUrl | None = None
    created_at: str | None = None
    updated_at: str | None = None


class SpecificationRevisionDownload(ProcoreModel):
    """Download metadata for a Procore specification section revision."""

    id: int | None = None
    number: str | int | None = None
    title: str | None = None
    revision_number: str | int | None = None
    filename: str | None = None
    file_name: str | None = None
    name: str | None = None
    url: str | HttpUrl | None = None
    download_url: str | HttpUrl | None = None
    file_url: str | HttpUrl | None = None
