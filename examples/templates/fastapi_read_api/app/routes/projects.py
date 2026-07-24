"""Read-only project routes for the copied starter."""

from app.config import get_config
from app.procore_client import get_procore_client
from fastapi import APIRouter

router = APIRouter(tags=["projects"])


@router.get("/projects")
def list_projects() -> dict[str, object]:
    """List projects visible to the configured company context."""
    config = get_config()
    company_id = config.company_id or 123456
    client = get_procore_client()
    return {
        "items": client.list_projects(company_id),
        "read_only": True,
        "write_actions_enabled": False,
    }
