"""Endpoint path definitions for the Procore REST API."""

from __future__ import annotations

API_V1 = "/rest/v1.0"
API_V1_1 = "/rest/v1.1"
API_V2 = "/rest/v2.0"
API_V2_1 = "/rest/v2.1"

COMPANIES = f"{API_V1}/companies"
PROJECTS = f"{API_V1}/companies/{{company_id}}/projects"
RFIS = f"{API_V1_1}/projects/{{project_id}}/rfis"
RFI = f"{API_V1_1}/projects/{{project_id}}/rfis/{{rfi_id}}"
SUBMITTALS = f"{API_V1_1}/projects/{{project_id}}/submittals"
SUBMITTAL = f"{API_V1_1}/projects/{{project_id}}/submittals/{{submittal_id}}"
# Procore Documents are exposed through the Project Folders and Files API.
# The project is supplied as a query parameter, not as a path segment.
DOCUMENT_FOLDERS = f"{API_V1}/folders"
DOCUMENT_FOLDER = f"{API_V1}/folders/{{folder_id}}"
DOCUMENTS = DOCUMENT_FOLDERS
DOCUMENT = f"{API_V1}/files/{{document_id}}"
# Procore Drawings are organized by project drawing areas. Drawing list and
# item endpoints are drawing-area scoped, while area and revision collections
# are project scoped.
DRAWING_AREAS = f"{API_V1}/projects/{{project_id}}/drawing_areas"
DRAWING_AREA = f"{API_V1}/projects/{{project_id}}/drawing_areas/{{drawing_area_id}}"
DRAWING_DISCIPLINES = f"{API_V1}/projects/{{project_id}}/drawing_disciplines"
DRAWINGS = f"{API_V1}/drawing_areas/{{drawing_area_id}}/drawings"
DRAWING = f"{API_V1}/drawing_areas/{{drawing_area_id}}/drawings/{{drawing_id}}"
DRAWING_REVISIONS = f"{API_V1}/projects/{{project_id}}/drawing_revisions"
IMAGE_CATEGORIES = f"{API_V1}/image_categories"
IMAGE_CATEGORY = f"{API_V1}/image_categories/{{image_category_id}}"
IMAGES = f"{API_V1}/images"
IMAGE = f"{API_V1}/images/{{image_id}}"
SPECIFICATION_SETS = f"{API_V2}/companies/{{company_id}}/projects/{{project_id}}/specification_sets"
SPECIFICATION_SET_V1 = (
    f"{API_V1}/projects/{{project_id}}/specification_sets/{{specification_set_id}}"
)
SPECIFICATION_SECTIONS = (
    f"{API_V2_1}/companies/{{company_id}}/projects/{{project_id}}/specification_sections"
)
SPECIFICATION_SECTION_REVISIONS = (
    f"{API_V2_1}/companies/{{company_id}}/projects/{{project_id}}"
    "/specification_section_revisions"
)
SPECIFICATION_SECTION_REVISION = (
    f"{API_V2_1}/companies/{{company_id}}/projects/{{project_id}}"
    "/specification_section_revisions/{revision_id}"
)
SPECIFICATION_SECTION_REVISION_DOWNLOAD = (
    f"{API_V2_1}/companies/{{company_id}}/projects/{{project_id}}"
    "/specification_section_revisions/{revision_id}/download"
)


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


def document_folders(project_id: int) -> str:
    """Return the project folders collection endpoint.

    Args:
        project_id: Procore project ID. The value is accepted for API
            consistency with service methods; callers pass it as a query
            parameter because Procore's Documents API uses ``/folders``.
    """
    return DOCUMENT_FOLDERS


def document_folder(project_id: int, folder_id: int) -> str:
    """Return the endpoint for a single project document folder."""
    return DOCUMENT_FOLDER.format(folder_id=folder_id)


def documents(project_id: int) -> str:
    """Return the folders/files collection endpoint used to list documents."""
    return DOCUMENTS


def document(project_id: int, document_id: int) -> str:
    """Return the endpoint for a single document file."""
    return DOCUMENT.format(document_id=document_id)


def drawing_areas(project_id: int) -> str:
    """Return the drawing areas collection endpoint for a project."""
    return DRAWING_AREAS.format(project_id=project_id)


def drawing_area(project_id: int, drawing_area_id: int) -> str:
    """Return the endpoint for a single drawing area."""
    return DRAWING_AREA.format(project_id=project_id, drawing_area_id=drawing_area_id)


def drawing_disciplines(project_id: int) -> str:
    """Return the drawing disciplines collection endpoint for a project."""
    return DRAWING_DISCIPLINES.format(project_id=project_id)


def drawings(project_id: int, drawing_area_id: int) -> str:
    """Return the drawings collection endpoint for a drawing area.

    Args:
        project_id: Procore project ID. Accepted for consistency with service
            methods; Procore scopes this endpoint by drawing area.
        drawing_area_id: Procore drawing area ID.
    """
    return DRAWINGS.format(drawing_area_id=drawing_area_id)


def drawing(project_id: int, drawing_area_id: int, drawing_id: int) -> str:
    """Return the endpoint for a single drawing."""
    return DRAWING.format(drawing_area_id=drawing_area_id, drawing_id=drawing_id)


def drawing_revisions(project_id: int) -> str:
    """Return the drawing revisions collection endpoint for a project."""
    return DRAWING_REVISIONS.format(project_id=project_id)


def image_categories() -> str:
    """Return the photo albums/image categories collection endpoint."""
    return IMAGE_CATEGORIES


def image_category(image_category_id: int) -> str:
    """Return the endpoint for one photo album/image category."""
    return IMAGE_CATEGORY.format(image_category_id=image_category_id)


def images() -> str:
    """Return the photos/images collection endpoint."""
    return IMAGES


def image(image_id: int) -> str:
    """Return the endpoint for one photo/image."""
    return IMAGE.format(image_id=image_id)


def specification_sets(company_id: int, project_id: int) -> str:
    """Return the specification sets collection endpoint for a project."""
    return SPECIFICATION_SETS.format(company_id=company_id, project_id=project_id)


def specification_set_v1(project_id: int, specification_set_id: int) -> str:
    """Return the legacy v1 specification set show endpoint."""
    return SPECIFICATION_SET_V1.format(
        project_id=project_id,
        specification_set_id=specification_set_id,
    )


def specification_sections(company_id: int, project_id: int) -> str:
    """Return the specification sections collection endpoint for a project."""
    return SPECIFICATION_SECTIONS.format(company_id=company_id, project_id=project_id)


def specification_section_revisions(company_id: int, project_id: int) -> str:
    """Return the specification section revisions collection endpoint."""
    return SPECIFICATION_SECTION_REVISIONS.format(
        company_id=company_id,
        project_id=project_id,
    )


def specification_section_revision(company_id: int, project_id: int, revision_id: int) -> str:
    """Return the endpoint for one specification section revision."""
    return SPECIFICATION_SECTION_REVISION.format(
        company_id=company_id,
        project_id=project_id,
        revision_id=revision_id,
    )


def specification_section_revision_download(
    company_id: int,
    project_id: int,
    revision_id: int,
) -> str:
    """Return the download-info endpoint for one specification revision."""
    return SPECIFICATION_SECTION_REVISION_DOWNLOAD.format(
        company_id=company_id,
        project_id=project_id,
        revision_id=revision_id,
    )


class Endpoints:
    """Backward-compatible namespace for endpoint path templates."""

    COMPANIES = COMPANIES
    PROJECTS = PROJECTS
    RFIS = RFIS
    RFI = RFI
    SUBMITTALS = SUBMITTALS
    SUBMITTAL = SUBMITTAL
    DOCUMENT_FOLDERS = DOCUMENT_FOLDERS
    DOCUMENT_FOLDER = DOCUMENT_FOLDER
    DOCUMENTS = DOCUMENTS
    DOCUMENT = DOCUMENT
    DRAWINGS = DRAWINGS
    DRAWING = DRAWING
    DRAWING_AREAS = DRAWING_AREAS
    DRAWING_AREA = DRAWING_AREA
    DRAWING_DISCIPLINES = DRAWING_DISCIPLINES
    DRAWING_REVISIONS = DRAWING_REVISIONS
    IMAGE_CATEGORIES = IMAGE_CATEGORIES
    IMAGE_CATEGORY = IMAGE_CATEGORY
    IMAGES = IMAGES
    IMAGE = IMAGE
    SPECIFICATION_SETS = SPECIFICATION_SETS
    SPECIFICATION_SET_V1 = SPECIFICATION_SET_V1
    SPECIFICATION_SECTIONS = SPECIFICATION_SECTIONS
    SPECIFICATION_SECTION_REVISIONS = SPECIFICATION_SECTION_REVISIONS
    SPECIFICATION_SECTION_REVISION = SPECIFICATION_SECTION_REVISION
    SPECIFICATION_SECTION_REVISION_DOWNLOAD = SPECIFICATION_SECTION_REVISION_DOWNLOAD
