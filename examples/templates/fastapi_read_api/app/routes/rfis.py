"""Read-only RFI routes for the copied starter."""

from app.procore_client import get_procore_client
from fastapi import APIRouter

router = APIRouter(tags=["rfis"])


@router.get("/projects/{project_id}/rfis")
def list_project_rfis(project_id: int) -> dict[str, object]:
    """List RFIs for a project using a read-only PyProcore helper."""
    client = get_procore_client()
    return {
        "items": client.list_rfis(project_id),
        "read_only": True,
        "write_actions_enabled": False,
    }
