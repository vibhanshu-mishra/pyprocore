"""Local analytics route using fake exported records only."""

from fastapi import APIRouter

from pyprocore.analytics import ProjectHealthInput, build_project_health_report

router = APIRouter(tags=["analytics"])


@router.get("/projects/{project_id}/analytics/project-health")
def project_health(project_id: int) -> dict[str, object]:
    """Return a deterministic local project-health example.

    This route uses fake in-memory records. It does not call Procore or any
    external AI/model API.
    """
    report = build_project_health_report(
        ProjectHealthInput(
            rfis=[
                {
                    "id": 1001,
                    "number": "15",
                    "status": "Open",
                    "created_at": "2026-01-01",
                    "due_date": "2026-01-15",
                }
            ],
            submittals=[
                {
                    "id": 2001,
                    "number": "27",
                    "status": "Pending",
                    "due_date": "2026-02-01",
                }
            ],
        )
    )
    payload = report.model_dump(mode="json")
    payload["project_id"] = project_id
    return payload
