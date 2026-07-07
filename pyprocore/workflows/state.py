"""Local state helpers for incremental workflow sync."""

from __future__ import annotations

import json
from pathlib import Path

from pyprocore.workflows.models import SyncState


def build_sync_state_path(output_dir: str | Path, item_type: str) -> Path:
    """Return the state file path for an output directory and item type."""
    safe_item_type = item_type.strip().lower() or "items"
    return Path(output_dir) / f".pyprocore-{safe_item_type}-sync-state.json"


def load_sync_state(path: str | Path) -> SyncState:
    """Load a sync state file.

    Args:
        path: State file path.

    Returns:
        Parsed sync state.
    """
    state_path = Path(path)
    return SyncState.model_validate(json.loads(state_path.read_text(encoding="utf-8")))


def save_sync_state(state: SyncState, path: str | Path) -> Path:
    """Save a sync state file and return its path."""
    state_path = Path(path)
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(
        json.dumps(state.model_dump(mode="json"), indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return state_path
