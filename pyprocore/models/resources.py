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
