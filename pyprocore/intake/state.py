"""Safe local JSON state tracking for intake polling."""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import ValidationError as PydanticValidationError

from pyprocore.core.exceptions import ValidationError
from pyprocore.intake.models import (
    IntakeSyncConfig,
    IntakeSyncRunResult,
    IntakeSyncState,
)


def build_initial_intake_sync_state(config: IntakeSyncConfig) -> IntakeSyncState:
    """Build empty local state for an intake configuration."""
    return IntakeSyncState(
        profile_name=config.profile_name,
        company_id=config.company_id,
        project_ids=config.project_ids,
    )


def load_intake_sync_state(path: str | Path) -> IntakeSyncState:
    """Load local intake state from JSON."""
    source = _json_path(path, reject_traversal=True)
    try:
        payload = json.loads(source.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ValidationError(f"Could not read intake state {source}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ValidationError(f"Intake state {source} is not valid JSON: {exc}") from exc
    try:
        return IntakeSyncState.model_validate(payload)
    except PydanticValidationError as exc:
        raise ValidationError(f"Invalid intake state {source}: {exc}") from exc


def save_intake_sync_state(
    state: IntakeSyncState,
    path: str | Path,
    *,
    overwrite: bool = False,
) -> Path:
    """Save local JSON state with explicit overwrite protection."""
    destination = _json_path(path, reject_traversal=True).resolve()
    if destination.exists() and not overwrite:
        raise ValidationError(
            f"Refusing to overwrite existing intake state: {destination}. "
            "Pass overwrite=True explicitly."
        )
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(state.model_dump(mode="json"), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return destination


def update_intake_sync_state_after_run(
    state: IntakeSyncState,
    result: IntakeSyncRunResult,
) -> IntakeSyncState:
    """Return state updated from a completed local intake result."""
    return result.state_after.model_copy(
        update={
            "profile_name": state.profile_name or result.config.profile_name,
            "company_id": state.company_id or result.config.company_id,
        }
    )


def _json_path(path: str | Path, *, reject_traversal: bool = False) -> Path:
    candidate = Path(path).expanduser()
    if reject_traversal and ".." in candidate.parts:
        raise ValidationError("Path traversal is not allowed for intake state.")
    if candidate.suffix.casefold() != ".json":
        raise ValidationError("Intake state files must be JSON.")
    return candidate
