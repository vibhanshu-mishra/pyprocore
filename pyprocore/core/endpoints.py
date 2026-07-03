"""Endpoint path definitions for the Procore REST API."""

from __future__ import annotations

API_V1 = "/rest/v1.0"
API_V1_1 = "/rest/v1.1"

COMPANIES = f"{API_V1}/companies"
PROJECTS = f"{API_V1}/companies/{{company_id}}/projects"
RFIS = f"{API_V1_1}/projects/{{project_id}}/rfis"
RFI = f"{API_V1_1}/projects/{{project_id}}/rfis/{{rfi_id}}"
SUBMITTALS = f"{API_V1_1}/projects/{{project_id}}/submittals"
SUBMITTAL = f"{API_V1_1}/projects/{{project_id}}/submittals/{{submittal_id}}"


def companies() -> str:
    """Return the companies collection endpoint."""
    return COMPANIES


def projects(company_id: int) -> str:
    """Return the projects collection endpoint for a company."""
    return PROJECTS.format(company_id=company_id)


def rfis(project_id: int) -> str:
    """Return the RFIs collection endpoint for a project."""
    return RFIS.format(project_id=project_id)


def rfi(project_id: int, rfi_id: int) -> str:
    """Return the endpoint for a single RFI."""
    return RFI.format(project_id=project_id, rfi_id=rfi_id)


def submittals(project_id: int) -> str:
    """Return the submittals collection endpoint for a project."""
    return SUBMITTALS.format(project_id=project_id)


def submittal(project_id: int, submittal_id: int) -> str:
    """Return the endpoint for a single submittal."""
    return SUBMITTAL.format(project_id=project_id, submittal_id=submittal_id)


class Endpoints:
    """Backward-compatible namespace for endpoint path templates."""

    COMPANIES = COMPANIES
    PROJECTS = PROJECTS
    RFIS = RFIS
    RFI = RFI
    SUBMITTALS = SUBMITTALS
    SUBMITTAL = SUBMITTAL
