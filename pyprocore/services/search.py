"""Human-friendly search and resolver helpers for Procore resources."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Sequence
from typing import TypeVar

from pyprocore.core.config import ProcoreSettings, get_settings
from pyprocore.core.exceptions import DuplicateMatchError, MultipleResultsError, NotFoundError
from pyprocore.models import (
    RFI,
    Company,
    Correspondence,
    Document,
    DocumentFolder,
    Drawing,
    Observation,
    Project,
    PunchItem,
    Submittal,
)
from pyprocore.services.companies import list_companies
from pyprocore.services.correspondence import list_correspondences
from pyprocore.services.documents import list_document_folders, list_documents
from pyprocore.services.drawings import list_drawings
from pyprocore.services.observations import list_observations
from pyprocore.services.projects import list_projects
from pyprocore.services.punch_items import list_punch_items
from pyprocore.services.rfis import list_rfis
from pyprocore.services.submittals import list_submittals

ResourceT = TypeVar("ResourceT")


def find_company(name: str) -> Company:
    """Find one company by name using case-insensitive exact or partial matching.

    Args:
        name: Company name or name fragment.

    Returns:
        The matching company.

    Raises:
        NotFoundError: If no company matches.
        DuplicateMatchError: If multiple exact matches are found.
        MultipleResultsError: If multiple partial matches are found.
    """
    query = _normalize_query(name, "name")
    return _resolve_one(
        resources=list_companies(),
        query=query,
        values=lambda company: [company.name],
        resource_name="company",
    )


def find_project(
    name: str | None = None,
    *,
    number: str | int | None = None,
    company_id: int | None = None,
    settings: ProcoreSettings | None = None,
) -> Project:
    """Find one project by name or project number.

    Args:
        name: Project name or name fragment.
        number: Project number to resolve.
        company_id: Optional company ID. Defaults to ``PROCORE_COMPANY_ID``.
        settings: Optional SDK settings used when ``company_id`` is omitted.

    Returns:
        The matching project.

    Raises:
        NotFoundError: If no project matches.
        DuplicateMatchError: If multiple exact matches are found.
        MultipleResultsError: If multiple partial matches are found.
    """
    query = _project_query(name=name, number=number)
    resolved_company_id = company_id or (settings or get_settings()).company_id
    return _resolve_one(
        resources=list_projects(resolved_company_id),
        query=query,
        values=lambda project: [project.name, project.project_number],
        resource_name="project",
    )


def find_project_contains(
    text: str,
    *,
    company_id: int | None = None,
    settings: ProcoreSettings | None = None,
) -> Project:
    """Find one project whose name or number contains text.

    Args:
        text: Text to search for in project names or numbers.
        company_id: Optional company ID. Defaults to ``PROCORE_COMPANY_ID``.
        settings: Optional SDK settings used when ``company_id`` is omitted.

    Returns:
        The matching project.

    Raises:
        NotFoundError: If no project contains the text.
        MultipleResultsError: If multiple projects contain the text.
    """
    query = _normalize_query(text, "text")
    resolved_company_id = company_id or (settings or get_settings()).company_id
    return _resolve_contains(
        resources=list_projects(resolved_company_id),
        query=query,
        values=lambda project: [project.name, project.project_number],
        resource_name="project",
    )


def find_rfi(project_id: int, *, number: str | int) -> RFI:
    """Find one RFI by number within a project.

    Args:
        project_id: Procore project ID.
        number: RFI number.

    Returns:
        The matching RFI.

    Raises:
        NotFoundError: If no RFI matches.
        DuplicateMatchError: If multiple exact matches are found.
        MultipleResultsError: If multiple partial matches are found.
    """
    query = _normalize_query(number, "number")
    return _resolve_one(
        resources=list_rfis(project_id),
        query=query,
        values=lambda rfi: [rfi.number],
        resource_name="RFI",
    )


def find_submittal(project_id: int, *, number: str | int) -> Submittal:
    """Find one submittal by number within a project.

    Args:
        project_id: Procore project ID.
        number: Submittal number.

    Returns:
        The matching submittal.

    Raises:
        NotFoundError: If no submittal matches.
        DuplicateMatchError: If multiple exact matches are found.
        MultipleResultsError: If multiple partial matches are found.
    """
    query = _normalize_query(number, "number")
    return _resolve_one(
        resources=list_submittals(project_id),
        query=query,
        values=lambda submittal: [submittal.number],
        resource_name="submittal",
    )


def find_document_folder(project_id: int, name: str) -> DocumentFolder:
    """Find one document folder by name within a project.

    Args:
        project_id: Procore project ID.
        name: Folder name or name fragment.

    Returns:
        The matching document folder.

    Raises:
        NotFoundError: If no folder matches.
        DuplicateMatchError: If multiple exact matches are found.
        MultipleResultsError: If multiple partial matches are found.
    """
    query = _normalize_query(name, "name")
    return _resolve_one(
        resources=list_document_folders(project_id),
        query=query,
        values=lambda folder: [folder.name, folder.path],
        resource_name="document folder",
    )


def find_document(
    project_id: int,
    *,
    name: str | None = None,
    filename: str | None = None,
) -> Document:
    """Find one document by name or filename within a project.

    Args:
        project_id: Procore project ID.
        name: Document name or name fragment.
        filename: Document filename or filename fragment.

    Returns:
        The matching document.

    Raises:
        NotFoundError: If no document matches.
        DuplicateMatchError: If multiple exact matches are found.
        MultipleResultsError: If multiple partial matches are found.
    """
    query = _document_query(name=name, filename=filename)
    return _resolve_one(
        resources=list_documents(project_id),
        query=query,
        values=lambda document: [document.name, document.filename, document.file_name],
        resource_name="document",
    )


def find_drawing(
    project_id: int,
    *,
    number: str | int | None = None,
    title: str | None = None,
    company_id: int | None = None,
) -> Drawing:
    """Find one drawing by number or title within a project.

    Args:
        project_id: Procore project ID.
        number: Drawing number or number fragment.
        title: Drawing title or title fragment.
        company_id: Optional company ID sent as ``Procore-Company-Id``.

    Returns:
        The matching drawing.

    Raises:
        NotFoundError: If no drawing matches.
        DuplicateMatchError: If multiple exact matches are found.
        MultipleResultsError: If multiple partial matches are found.
    """
    query = _drawing_query(number=number, title=title)
    return _resolve_one(
        resources=list_drawings(project_id, company_id=company_id),
        query=query,
        values=lambda drawing: [drawing.number, drawing.title, drawing.name],
        resource_name="drawing",
    )


def find_drawings_contains(
    project_id: int,
    text: str,
    *,
    company_id: int | None = None,
) -> list[Drawing]:
    """Find drawings whose number, title, or name contains text.

    Args:
        project_id: Procore project ID.
        text: Text to search for.
        company_id: Optional company ID sent as ``Procore-Company-Id``.

    Returns:
        Matching drawings.

    Raises:
        NotFoundError: If no drawing contains the text.
    """
    query = _normalize_query(text, "text")
    matches = [
        drawing
        for drawing in list_drawings(project_id, company_id=company_id)
        if any(
            query in _normalized_value(value)
            for value in (drawing.number, drawing.title, drawing.name)
        )
    ]
    if not matches:
        raise NotFoundError(f"No drawing matched {query!r}.")
    return matches


def find_observation(
    company_id: int | None,
    project_id: int,
    *,
    number: str | int | None = None,
    title: str | None = None,
    query: str | None = None,
) -> Observation:
    """Find one observation by number, title, name, or description.

    Args:
        company_id: Optional company ID sent as ``Procore-Company-Id``.
        project_id: Procore project ID.
        number: Observation number or number fragment.
        title: Observation title or title fragment.
        query: General text search across common observation fields.

    Returns:
        The matching observation.

    Raises:
        NotFoundError: If no observation matches.
        DuplicateMatchError: If multiple exact matches are found.
        MultipleResultsError: If multiple partial matches are found.
    """
    search_text = _number_title_query(
        resource_name="observation",
        number=number,
        title=title,
        query=query,
    )
    return _resolve_one(
        resources=list_observations(company_id, project_id),
        query=search_text,
        values=lambda observation: [
            observation.number,
            observation.title,
            observation.name,
            observation.description,
        ],
        resource_name="observation",
    )


def find_punch_item(
    company_id: int | None,
    project_id: int,
    *,
    number: str | int | None = None,
    title: str | None = None,
    query: str | None = None,
) -> PunchItem:
    """Find one punch item by number, title, name, or description."""
    search_text = _number_title_query(
        resource_name="punch item",
        number=number,
        title=title,
        query=query,
    )
    return _resolve_one(
        resources=list_punch_items(company_id, project_id),
        query=search_text,
        values=lambda punch_item: [
            punch_item.number,
            punch_item.title,
            punch_item.name,
            punch_item.description,
        ],
        resource_name="punch item",
    )


def find_correspondence(
    company_id: int | None,
    project_id: int,
    generic_tool_id: int,
    *,
    number: str | int | None = None,
    title: str | None = None,
    query: str | None = None,
) -> Correspondence:
    """Find one Generic Tool item by number, subject, title, name, or description."""
    search_text = _number_title_query(
        resource_name="correspondence",
        number=number,
        title=title,
        query=query,
    )
    return _resolve_one(
        resources=list_correspondences(company_id, project_id, generic_tool_id),
        query=search_text,
        values=lambda correspondence: [
            correspondence.number,
            correspondence.subject,
            correspondence.title,
            correspondence.name,
            correspondence.description,
        ],
        resource_name="correspondence",
    )


def _resolve_one(
    *,
    resources: Sequence[ResourceT],
    query: str,
    values: Callable[[ResourceT], Iterable[object | None]],
    resource_name: str,
) -> ResourceT:
    """Resolve one resource using exact matching before partial matching."""
    exact_matches = [
        resource
        for resource in resources
        if any(_normalized_value(value) == query for value in values(resource))
    ]
    if len(exact_matches) == 1:
        return exact_matches[0]
    if len(exact_matches) > 1:
        raise DuplicateMatchError(
            f"Found {len(exact_matches)} exact {resource_name} matches for {query!r}."
        )

    return _resolve_contains(
        resources=resources,
        query=query,
        values=values,
        resource_name=resource_name,
    )


def _resolve_contains(
    *,
    resources: Sequence[ResourceT],
    query: str,
    values: Callable[[ResourceT], Iterable[object | None]],
    resource_name: str,
) -> ResourceT:
    """Resolve one resource using case-insensitive partial matching."""
    partial_matches = [
        resource
        for resource in resources
        if any(query in _normalized_value(value) for value in values(resource))
    ]
    if len(partial_matches) == 1:
        return partial_matches[0]
    if not partial_matches:
        raise NotFoundError(f"No {resource_name} matched {query!r}.")

    raise MultipleResultsError(
        f"Found {len(partial_matches)} {resource_name} matches for {query!r}."
    )


def _project_query(name: str | None, number: str | int | None) -> str:
    """Return the normalized project search query."""
    if name is not None and number is not None:
        raise ValueError("Pass either name or number, not both.")
    if name is None and number is None:
        raise ValueError("Project name or number is required.")
    return _normalize_query(number if number is not None else name, "project")


def _document_query(name: str | None, filename: str | None) -> str:
    """Return the normalized document search query."""
    if name is not None and filename is not None:
        raise ValueError("Pass either name or filename, not both.")
    if name is None and filename is None:
        raise ValueError("Document name or filename is required.")
    return _normalize_query(filename if filename is not None else name, "document")


def _drawing_query(number: str | int | None, title: str | None) -> str:
    """Return the normalized drawing search query."""
    if number is not None and title is not None:
        raise ValueError("Pass either number or title, not both.")
    if number is None and title is None:
        raise ValueError("Drawing number or title is required.")
    return _normalize_query(number if number is not None else title, "drawing")


def _number_title_query(
    *,
    resource_name: str,
    number: str | int | None,
    title: str | None,
    query: str | None,
) -> str:
    """Return a normalized resource search query."""
    provided = [value for value in (number, title, query) if value is not None]
    if len(provided) > 1:
        raise ValueError(f"Pass only one {resource_name} search value.")
    if not provided:
        raise ValueError(f"{resource_name.title()} number, title, or query is required.")
    return _normalize_query(provided[0], resource_name)


def _normalize_query(value: object | None, field_name: str) -> str:
    """Normalize a user-provided search query."""
    if value is None:
        raise ValueError(f"{field_name} is required.")

    normalized = str(value).casefold().strip()
    if not normalized:
        raise ValueError(f"{field_name} cannot be blank.")
    return normalized


def _normalized_value(value: object | None) -> str:
    """Normalize a resource field for matching."""
    return "" if value is None else str(value).casefold().strip()
