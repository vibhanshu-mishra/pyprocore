"""User-facing local analytics recipe helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pyprocore.analytics.loaders import load_records_from_path
from pyprocore.analytics.models import ProjectHealthInput, ProjectHealthRecipeResult
from pyprocore.analytics.scoring import (
    analyze_change_exposure,
    analyze_daily_log_completeness,
    analyze_rfi_aging,
    analyze_submittal_delay,
    build_project_health_report,
)


def run_rfi_aging_recipe(path: Path | str) -> ProjectHealthRecipeResult:
    """Run the RFI aging recipe against a local JSON, JSONL, or CSV file."""
    summary = analyze_rfi_aging(load_records_from_path(path))
    return ProjectHealthRecipeResult(recipe="rfi_aging", summary=summary)


def run_submittal_delay_recipe(path: Path | str) -> ProjectHealthRecipeResult:
    """Run the submittal delay recipe against a local JSON, JSONL, or CSV file."""
    summary = analyze_submittal_delay(load_records_from_path(path))
    return ProjectHealthRecipeResult(recipe="submittal_delay", summary=summary)


def run_change_exposure_recipe(path: Path | str) -> ProjectHealthRecipeResult:
    """Run the change exposure recipe against a local JSON, JSONL, or CSV file."""
    summary = analyze_change_exposure(load_records_from_path(path))
    return ProjectHealthRecipeResult(recipe="change_exposure", summary=summary)


def run_daily_log_completeness_recipe(
    path: Path | str,
    *,
    start_date: str | None = None,
    end_date: str | None = None,
) -> ProjectHealthRecipeResult:
    """Run the daily log completeness recipe against a local file."""
    summary = analyze_daily_log_completeness(
        load_records_from_path(path),
        start_date=start_date,
        end_date=end_date,
    )
    return ProjectHealthRecipeResult(recipe="daily_log_completeness", summary=summary)


def run_project_health_recipe(
    *,
    rfis_path: Path | str | None = None,
    submittals_path: Path | str | None = None,
    changes_path: Path | str | None = None,
    daily_logs_path: Path | str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
) -> ProjectHealthRecipeResult:
    """Run the combined project health recipe against local files."""
    project_input = ProjectHealthInput(
        rfis=load_records_from_path(rfis_path) if rfis_path else [],
        submittals=load_records_from_path(submittals_path) if submittals_path else [],
        changes=load_records_from_path(changes_path) if changes_path else [],
        daily_logs=load_records_from_path(daily_logs_path) if daily_logs_path else [],
    )
    summary = build_project_health_report(
        project_input,
        start_date=start_date,
        end_date=end_date,
    )
    return ProjectHealthRecipeResult(recipe="project_health", summary=summary)


def write_sample_analytics_data(output_dir: Path | str) -> list[Path]:
    """Write fake local analytics datasets for examples and CLI demos."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    files = {
        "fake_rfis.json": _sample_rfis(),
        "fake_submittals.json": _sample_submittals(),
        "fake_changes.json": _sample_changes(),
        "fake_daily_logs.json": _sample_daily_logs(),
    }
    written: list[Path] = []
    for filename, records in files.items():
        path = output_path / filename
        path.write_text(json.dumps(records, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        written.append(path)
    return written


def sample_analytics_data() -> dict[str, list[dict[str, Any]]]:
    """Return fake in-memory local analytics records."""
    return {
        "rfis": _sample_rfis(),
        "submittals": _sample_submittals(),
        "changes": _sample_changes(),
        "daily_logs": _sample_daily_logs(),
    }


def _sample_rfis() -> list[dict[str, Any]]:
    return [
        {
            "id": 1001,
            "number": "15",
            "title": "Confirm lobby ceiling detail",
            "status": "Open",
            "created_at": "2026-06-01",
            "due_date": "2026-06-15",
            "ball_in_court": "Architect",
            "schedule_impact": "TBD",
        },
        {
            "id": 1002,
            "number": "16",
            "title": "Clarify door hardware finish",
            "status": "Closed",
            "created_at": "2026-06-10",
            "due_date": "2026-06-20",
        },
    ]


def _sample_submittals() -> list[dict[str, Any]]:
    return [
        {
            "id": 2001,
            "number": "27",
            "title": "Storefront glazing",
            "status": "Pending",
            "due_date": "2026-06-18",
            "required_on_site_date": "2026-07-10",
            "ball_in_court": "Reviewer",
        },
        {
            "id": 2002,
            "number": "28",
            "title": "Paint samples",
            "status": "Approved",
            "due_date": "2026-06-22",
        },
    ]


def _sample_changes() -> list[dict[str, Any]]:
    return [
        {
            "id": 3001,
            "number": "CE-001",
            "title": "Lobby framing revision",
            "status": "Open",
            "estimated_exposure": 42000,
        },
        {
            "id": 3002,
            "number": "PCO-002",
            "title": "Owner finish upgrade",
            "status": "Approved",
            "estimated_exposure": 18000,
        },
    ]


def _sample_daily_logs() -> list[dict[str, Any]]:
    return [
        {"id": 4001, "date": "2026-06-01", "log_type": "manpower", "entry_count": 3},
        {"id": 4002, "date": "2026-06-02", "log_type": "weather", "entry_count": 1},
        {"id": 4003, "date": "2026-06-04", "log_type": "manpower", "entry_count": 2},
    ]
