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
