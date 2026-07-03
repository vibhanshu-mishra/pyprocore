"""Company service for the Procore SDK."""

from __future__ import annotations

from pyprocore.core import endpoints
from pyprocore.core.client import ProcoreClient
from pyprocore.models import Company


class CompaniesService:
    """Service for Procore company resources."""

    def __init__(self, client: ProcoreClient | None = None) -> None:
        """Initialize the service.

        Args:
            client: Optional shared Procore HTTP client.
        """
        self._client = client or ProcoreClient()

    def list_companies(self) -> list[Company]:
        """Return companies available to the authenticated Procore user."""
        response = self._client.get_all(endpoints.companies())
        return [Company.model_validate(company) for company in response]


def list_companies(client: ProcoreClient | None = None) -> list[Company]:
    """Return companies available to the authenticated Procore user."""
    return CompaniesService(client=client).list_companies()
