"""Human-friendly search and resolver helpers for Procore resources."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Sequence
from typing import TypeVar

from pyprocore.core.config import ProcoreSettings, get_settings
from pyprocore.core.exceptions import DuplicateMatchError, MultipleResultsError, NotFoundError
from pyprocore.models import RFI, Company, Project, Submittal
from pyprocore.services.companies import list_companies
from pyprocore.services.projects import list_projects
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
