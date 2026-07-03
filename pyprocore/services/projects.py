"""Project service for the Procore SDK."""

from __future__ import annotations

from pyprocore.core import endpoints
from pyprocore.core.client import ProcoreClient
from pyprocore.core.config import ProcoreSettings, get_settings
from pyprocore.core.exceptions import ResourceNotFoundError, ValidationError
from pyprocore.models import Project


class ProjectsService:
    """Service for Procore project resources."""

    def __init__(
        self,
        client: ProcoreClient | None = None,
        settings: ProcoreSettings | None = None,
    ) -> None:
        """Initialize the service.

        Args:
            client: Optional shared Procore HTTP client.
            settings: Optional SDK settings. Used for the default company ID.
        """
        self._client = client or ProcoreClient()
        self._settings = settings or get_settings()

    def list_projects(self, company_id: int) -> list[Project]:
        """Return projects for a Procore company.

        Args:
            company_id: Procore company ID.

        Returns:
            A list of project records.
        """
        if company_id <= 0:
            raise ValidationError("company_id must be a positive integer.")

        response = self._client.get_all(endpoints.projects(company_id))
        return [Project.model_validate(project) for project in response]

    def get_project(self, project_id: int) -> Project:
        """Return a single project from the configured company.

        This uses the verified company projects endpoint and finds the requested
        project locally instead of relying on an unverified single-project path.

        Args:
            project_id: Procore project ID.

        Returns:
            The matching project record.

        Raises:
            ResourceNotFoundError: If the configured company does not contain
                the requested project.
        """
        if project_id <= 0:
            raise ValidationError("project_id must be a positive integer.")

        for project in self.list_projects(self._settings.company_id):
            if project.id == project_id:
                return project

        raise ResourceNotFoundError(
            f"Project {project_id} was not found for company {self._settings.company_id}."
        )


def list_projects(
    company_id: int,
    client: ProcoreClient | None = None,
) -> list[Project]:
    """Return projects for a Procore company."""
    return ProjectsService(client=client).list_projects(company_id)


def get_project(
    project_id: int,
    client: ProcoreClient | None = None,
) -> Project:
    """Return a single project from the configured company."""
    return ProjectsService(client=client).get_project(project_id)
