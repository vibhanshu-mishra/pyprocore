"""Object-oriented client interface for PyProcore services."""

from __future__ import annotations

import builtins
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from pyprocore.core.config import get_settings
from pyprocore.models import RFI, Company, Project, Submittal
from pyprocore.services import (
    download_rfi_attachments,
    download_submittal_attachments,
    find_company,
    find_project,
    find_project_contains,
    find_rfi,
    find_submittal,
    get_project,
    get_rfi,
    get_submittal,
    list_companies,
    list_projects,
    list_rfis,
    list_submittals,
)


class CompaniesClient:
    """Convenience methods for Procore company resources."""

    def list(self) -> list[Company]:
        """List companies available to the authenticated Procore user.

        Returns:
            A list of typed company models.
        """
        return list_companies()

    def find(self, name: str) -> Company:
        """Find one company by name or name fragment.

        Args:
            name: Company name or partial name.

        Returns:
            The matching typed company model.
        """
        return find_company(name)


class ProjectsClient:
    """Convenience methods for Procore project resources."""

    def list(self, company_id: int | None = None) -> list[Project]:
        """List projects for a Procore company.

        Args:
            company_id: Optional Procore company ID. Defaults to
                ``PROCORE_COMPANY_ID``.

        Returns:
            A list of typed project models.
        """
        resolved_company_id = company_id or get_settings().company_id
        return list_projects(company_id=resolved_company_id)

    def get(self, project_id: int) -> Project:
        """Get one project from the configured company.

        Args:
            project_id: Procore project ID.

        Returns:
            The matching typed project model.
        """
        return get_project(project_id=project_id)

    def find(
        self,
        name: str | None = None,
        *,
        number: str | int | None = None,
        company_id: int | None = None,
    ) -> Project:
        """Find one project by name or project number.

        Args:
            name: Project name or name fragment.
            number: Project number.
            company_id: Optional company ID. Defaults to ``PROCORE_COMPANY_ID``.

        Returns:
            The matching typed project model.
        """
        return find_project(name=name, number=number, company_id=company_id)

    def find_contains(self, text: str, *, company_id: int | None = None) -> Project:
        """Find one project whose name or number contains text.

        Args:
            text: Text to search for in project names or numbers.
            company_id: Optional company ID. Defaults to ``PROCORE_COMPANY_ID``.

        Returns:
            The matching typed project model.
        """
        return find_project_contains(text, company_id=company_id)


class RFIsClient:
    """Convenience methods for Procore RFI resources."""

    def list(
        self,
        project_id: int,
        *,
        status: str | None = None,
        updated_after: str | None = None,
        updated_before: str | None = None,
        created_after: str | None = None,
        created_before: str | None = None,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[RFI]:
        """List RFIs for a Procore project.

        Args:
            project_id: Procore project ID.
            status: Optional RFI status filter.
            updated_after: Optional lower bound for updated date filtering.
            updated_before: Optional upper bound for updated date filtering.
            created_after: Optional lower bound for created date filtering.
            created_before: Optional upper bound for created date filtering.
            params: Optional additional query parameters.
            **extra_params: Additional query parameters passed to Procore.

        Returns:
            A list of typed RFI models.
        """
        return list_rfis(
            project_id=project_id,
            status=status,
            updated_after=updated_after,
            updated_before=updated_before,
            created_after=created_after,
            created_before=created_before,
            params=params,
            **extra_params,
        )

    def get(self, project_id: int, rfi_id: int) -> RFI:
        """Get one RFI by project ID and RFI ID.

        Args:
            project_id: Procore project ID.
            rfi_id: Procore RFI ID.

        Returns:
            The matching typed RFI model.
        """
        return get_rfi(project_id=project_id, rfi_id=rfi_id)

    def find(self, project_id: int, *, number: str | int) -> RFI:
        """Find one RFI by number within a project.

        Args:
            project_id: Procore project ID.
            number: RFI number.

        Returns:
            The matching typed RFI model.
        """
        return find_rfi(project_id=project_id, number=number)

    def download_attachments(
        self,
        project_id: int,
        rfi_id: int,
        output_dir: Path | str | None = None,
        *,
        overwrite: bool = False,
    ) -> builtins.list[Path]:
        """Download all attachments from one RFI.

        Args:
            project_id: Procore project ID.
            rfi_id: Procore RFI ID.
            output_dir: Optional local directory for downloaded files.
            overwrite: Whether to overwrite existing files.

        Returns:
            Paths to downloaded files.
        """
        return download_rfi_attachments(
            project_id=project_id,
            rfi_id=rfi_id,
            destination_dir=output_dir,
            overwrite=overwrite,
        )


class SubmittalsClient:
    """Convenience methods for Procore submittal resources."""

    def list(
        self,
        project_id: int,
        *,
        status: str | None = None,
        updated_after: str | None = None,
        updated_before: str | None = None,
        created_after: str | None = None,
        created_before: str | None = None,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[Submittal]:
        """List submittals for a Procore project.

        Args:
            project_id: Procore project ID.
            status: Optional submittal status filter.
            updated_after: Optional lower bound for updated date filtering.
            updated_before: Optional upper bound for updated date filtering.
            created_after: Optional lower bound for created date filtering.
            created_before: Optional upper bound for created date filtering.
            params: Optional additional query parameters.
            **extra_params: Additional query parameters passed to Procore.

        Returns:
            A list of typed submittal models.
        """
        return list_submittals(
            project_id=project_id,
            status=status,
            updated_after=updated_after,
            updated_before=updated_before,
            created_after=created_after,
            created_before=created_before,
            params=params,
            **extra_params,
        )

    def get(self, project_id: int, submittal_id: int) -> Submittal:
        """Get one submittal by project ID and submittal ID.

        Args:
            project_id: Procore project ID.
            submittal_id: Procore submittal ID.

        Returns:
            The matching typed submittal model.
        """
        return get_submittal(project_id=project_id, submittal_id=submittal_id)

    def find(self, project_id: int, *, number: str | int) -> Submittal:
        """Find one submittal by number within a project.

        Args:
            project_id: Procore project ID.
            number: Submittal number.

        Returns:
            The matching typed submittal model.
        """
        return find_submittal(project_id=project_id, number=number)

    def download_attachments(
        self,
        project_id: int,
        submittal_id: int,
        output_dir: Path | str | None = None,
        *,
        overwrite: bool = False,
    ) -> builtins.list[Path]:
        """Download all attachments from one submittal.

        Args:
            project_id: Procore project ID.
            submittal_id: Procore submittal ID.
            output_dir: Optional local directory for downloaded files.
            overwrite: Whether to overwrite existing files.

        Returns:
            Paths to downloaded files.
        """
        return download_submittal_attachments(
            project_id=project_id,
            submittal_id=submittal_id,
            destination_dir=output_dir,
            overwrite=overwrite,
        )


class Procore:
    """Beginner-friendly object-oriented entry point for PyProcore.

    The grouped clients call the same service functions that PyProcore already
    exposes. Use this interface when you prefer discoverable dot notation such
    as ``client.projects.list(company_id=123456)``.
    """

    def __init__(self) -> None:
        """Create grouped service clients."""
        self.companies = CompaniesClient()
        self.projects = ProjectsClient()
        self.rfis = RFIsClient()
        self.submittals = SubmittalsClient()


__all__ = [
    "CompaniesClient",
    "Procore",
    "ProjectsClient",
    "RFIsClient",
    "SubmittalsClient",
]
