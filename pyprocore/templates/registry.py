"""Registry for optional local PyProcore starter templates."""

from __future__ import annotations

from collections.abc import Iterable

from pyprocore.core.exceptions import NotFoundError
from pyprocore.templates.models import StarterTemplateFile, StarterTemplateMetadata

FASTAPI_READ_API_TEMPLATE_NAME = "fastapi-read-api"


def list_starter_templates() -> list[StarterTemplateMetadata]:
    """Return all registered optional starter templates."""
    return [_fastapi_read_api_template()]


def get_starter_template(name: str) -> StarterTemplateMetadata:
    """Return a starter template by name.

    Args:
        name: Template identifier such as ``fastapi-read-api``.

    Raises:
        NotFoundError: If the template name is unknown.
    """
    normalized = name.strip().casefold()
    for template in list_starter_templates():
        if template.name.casefold() == normalized:
            return template
    raise NotFoundError(f"Starter template not found: {name}")


def iter_template_files(name: str) -> Iterable[StarterTemplateFile]:
    """Yield static files for a starter template."""
    return get_starter_template(name).files


def _fastapi_read_api_template() -> StarterTemplateMetadata:
    """Build the optional FastAPI read API starter template metadata."""
    files = [
        StarterTemplateFile(
            path="README.md",
            description="Starter instructions and safety boundaries.",
            content=_readme_template(),
        ),
        StarterTemplateFile(
            path="requirements.txt",
            description="Optional dependencies for the copied FastAPI starter only.",
            content="fastapi>=0.111\nuvicorn>=0.30\npytest>=8.0\npyprocore>=2.3.0\n",
        ),
        StarterTemplateFile(
            path=".env.example",
            description="Placeholder environment variables with no secrets.",
            content=_env_template(),
        ),
        StarterTemplateFile(
            path="app/main.py",
            description="Minimal FastAPI app wiring read-only routers.",
            content=_main_template(),
        ),
        StarterTemplateFile(
            path="app/__init__.py",
            description="Package marker for the copied starter app.",
            content='"""Optional copied FastAPI starter app package."""\n',
        ),
        StarterTemplateFile(
            path="app/config.py",
            description="Environment helper for the copied starter app.",
            content=_config_template(),
        ),
        StarterTemplateFile(
            path="app/procore_client.py",
            description="User-managed PyProcore client factory placeholder.",
            content=_client_template(),
        ),
        StarterTemplateFile(
            path="app/routes/projects.py",
            description="Read-only project listing route.",
            content=_projects_route_template(),
        ),
        StarterTemplateFile(
            path="app/routes/__init__.py",
            description="Route package marker for the copied starter app.",
            content='"""Read-only route modules for the copied FastAPI starter."""\n',
        ),
        StarterTemplateFile(
            path="app/routes/rfis.py",
            description="Read-only RFI listing route.",
            content=_rfis_route_template(),
        ),
        StarterTemplateFile(
            path="app/routes/submittals.py",
            description="Read-only submittal listing route.",
            content=_submittals_route_template(),
        ),
        StarterTemplateFile(
            path="app/routes/analytics.py",
            description="Local mocked analytics route using Phase 17D recipes.",
            content=_analytics_route_template(),
        ),
        StarterTemplateFile(
            path="app/routes/health.py",
            description="Local health route with safety flags.",
            content=_health_route_template(),
        ),
        StarterTemplateFile(
            path="tests/test_routes_mocked.py",
            description="Mocked tests that do not call Procore.",
            content=_tests_template(),
        ),
        StarterTemplateFile(
            path="scripts/run_local.sh",
            description="Optional local run helper for copied projects.",
            content=_run_script_template(),
        ),
    ]
    return StarterTemplateMetadata(
        name=FASTAPI_READ_API_TEMPLATE_NAME,
        title="FastAPI Read API Starter",
        summary=(
            "Optional copied starter template for a read-only FastAPI backend powered by "
            "PyProcore."
        ),
        category="optional_backend_example",
        files=files,
        safety_boundaries=[
            "Template files are static examples and are not part of PyProcore runtime.",
            "FastAPI is optional and uvicorn is optional in the copied template only.",
            "PyProcore does not host this app or store credentials.",
            "Routes are read-only and include no Procore create/update/delete/upload actions.",
            "MCP execution and Procore tool execution remain disabled.",
            "No external AI/model calls are included.",
            "Template tests use mocked clients and local fake data only.",
        ],
        optional_dependencies=["fastapi", "uvicorn"],
        read_only_routes=[
            "GET /health",
            "GET /projects",
            "GET /projects/{project_id}/rfis",
            "GET /projects/{project_id}/submittals",
            "GET /projects/{project_id}/analytics/project-health",
        ],
        notes=[
            "Users are responsible for production auth, deployment, rate limits, monitoring, "
            "and secret storage.",
            "Copying this template does not install dependencies or run the app.",
        ],
    )


def _readme_template() -> str:
    return """# PyProcore FastAPI Read API Starter

This is an optional starter template for building a small read-only FastAPI
backend with PyProcore.

## Safety Boundaries

- This folder is a copied starter template, not PyProcore runtime code.
- FastAPI and uvicorn are optional dependencies for this copied template only.
- PyProcore does not host this app.
- PyProcore does not store credentials.
- Use environment variables or your own secret manager.
- No Procore writes, uploads, approvals, payments, or delete routes are included.
- No MCP execution or Procore tool execution is included.
- No external AI/model calls are included.
- Tests use mocked clients and local fake data only.

## Local Setup

```bash
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install -r requirements.txt
cp .env.example .env
```

Fill in `.env` with your own local values. Do not commit `.env`.

## Run Locally

```bash
./scripts/run_local.sh
```

The starter exposes read-only routes:

- `GET /health`
- `GET /projects`
- `GET /projects/{project_id}/rfis`
- `GET /projects/{project_id}/submittals`
- `GET /projects/{project_id}/analytics/project-health`

## Tests

```bash
python3 -m pytest tests
```

The included tests are mocked examples. They should not call Procore.

## Production Notes

Before using this pattern in production, add your own authentication,
authorization, rate-limit handling, monitoring, logging policy, deployment
process, and secret storage. Keep routes read-only unless you intentionally
design and review a separate write-safe integration.
"""


def _env_template() -> str:
    return """# Placeholder values only. Do not commit real secrets.
PROCORE_COMPANY_ID=123456
PROCORE_PROJECT_ID=352338
PYPROCORE_USE_FAKE_CLIENT=true
"""


def _main_template() -> str:
    return '''"""Optional FastAPI read API starter for PyProcore.

This copied template is not part of the PyProcore runtime and does not run
unless you install its optional dependencies and start it yourself.
"""

from app.routes import analytics, health, projects, rfis, submittals
from fastapi import FastAPI

app = FastAPI(title="PyProcore Read API Starter")

app.include_router(health.router)
app.include_router(projects.router)
app.include_router(rfis.router)
app.include_router(submittals.router)
app.include_router(analytics.router)
'''


def _config_template() -> str:
    return '''"""Configuration helpers for the optional copied FastAPI starter."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class AppConfig:
    """Minimal starter configuration loaded from environment variables."""

    company_id: int | None
    project_id: int | None
    use_fake_client: bool = True


def _optional_int(value: str | None) -> int | None:
    return int(value) if value and value.isdigit() else None


def get_config() -> AppConfig:
    """Return local starter configuration without reading secrets."""
    return AppConfig(
        company_id=_optional_int(os.getenv("PROCORE_COMPANY_ID")),
        project_id=_optional_int(os.getenv("PROCORE_PROJECT_ID")),
        use_fake_client=os.getenv("PYPROCORE_USE_FAKE_CLIENT", "true").casefold() == "true",
    )
'''


def _client_template() -> str:
    return '''"""PyProcore client factory placeholder for the copied starter.

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
'''


def _projects_route_template() -> str:
    return '''"""Read-only project routes for the copied starter."""

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
'''


def _rfis_route_template() -> str:
    return '''"""Read-only RFI routes for the copied starter."""

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
'''


def _submittals_route_template() -> str:
    return '''"""Read-only submittal routes for the copied starter."""

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
'''


def _analytics_route_template() -> str:
    return '''"""Local analytics route using fake exported records only."""

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
'''


def _health_route_template() -> str:
    return '''"""Health and safety route for the copied starter."""

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
'''


def _tests_template() -> str:
    return '''"""Mocked tests for the copied FastAPI read API starter."""

from app.main import app
from fastapi.testclient import TestClient


def test_health_route_is_read_only() -> None:
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["read_only"] is True
    assert payload["procore_write_actions_enabled"] is False


def test_project_routes_use_fake_client() -> None:
    client = TestClient(app)
    response = client.get("/projects")
    assert response.status_code == 200
    assert response.json()["write_actions_enabled"] is False


def test_project_health_uses_local_fake_data() -> None:
    client = TestClient(app)
    response = client.get("/projects/352338/analytics/project-health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["project_id"] == 352338
    assert payload["procore_api_call_required"] is False
    assert payload["external_ai_call_required"] is False
    assert payload["write_actions_enabled"] is False
'''


def _run_script_template() -> str:
    return """#!/usr/bin/env bash
set -euo pipefail

echo "Starting optional PyProcore FastAPI read API starter..."
echo "No Procore writes, MCP execution, or external AI/model calls are included."
python3 -m uvicorn app.main:app --reload
"""
