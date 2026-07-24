"""PyProcore client factory placeholder for the copied starter.

The fake client keeps tests and first runs local. Replace it with a user-managed
PyProcore client only after you have configured auth and secret storage.
"""

from __future__ import annotations

from typing import Any

from app.config import get_config

from pyprocore import Procore


class FakeProcoreClient:
    """Small mocked read-only client for local starter routes."""

    def list_projects(self, company_id: int) -> list[dict[str, Any]]:
        return [{"id": 352338, "name": "Example Project", "company_id": company_id}]

    def list_rfis(self, project_id: int) -> list[dict[str, Any]]:
        return [{"id": 1001, "number": "15", "status": "Open", "project_id": project_id}]

    def list_submittals(self, project_id: int) -> list[dict[str, Any]]:
        return [{"id": 2001, "number": "27", "status": "Pending", "project_id": project_id}]


def get_procore_client() -> FakeProcoreClient | Procore:
    """Return a fake client by default, or a user-managed PyProcore client.

    TODO: For real use, configure OAuth and secret storage before setting
    PYPROCORE_USE_FAKE_CLIENT=false. Keep routes read-only.
    """
    config = get_config()
    if config.use_fake_client:
        return FakeProcoreClient()
    return Procore()
