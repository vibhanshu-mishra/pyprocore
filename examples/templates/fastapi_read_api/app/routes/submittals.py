"""Read-only submittal routes for the copied starter."""

from app.procore_client import get_procore_client
from fastapi import APIRouter

router = APIRouter(tags=["submittals"])


@router.get("/projects/{project_id}/submittals")
def list_project_submittals(project_id: int) -> dict[str, object]:
    """List submittals for a project using a read-only PyProcore helper."""
    client = get_procore_client()
    return {
        "items": client.list_submittals(project_id),
        "read_only": True,
        "write_actions_enabled": False,
    }
