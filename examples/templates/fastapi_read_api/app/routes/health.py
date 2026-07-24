"""Health and safety route for the copied starter."""

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict[str, object]:
    """Return local app health and safety flags."""
    return {
        "status": "ok",
        "read_only": True,
        "procore_write_actions_enabled": False,
        "mcp_execution_enabled": False,
        "external_ai_call_required": False,
    }
