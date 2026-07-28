"""Preview local intake output files without writing anything."""

import json
from pathlib import Path

from pyprocore.intake import (
    intake_to_json,
    load_intake_sync_config,
    run_intake_sync_with_records,
    write_intake_sync_outputs,
)

ROOT = Path(__file__).resolve().parents[1]


def _load(name: str) -> dict[str, list[dict[str, object]]]:
    return json.loads((ROOT / f"examples/intake/{name}").read_text(encoding="utf-8"))


def main() -> None:
    """Print planned paths while making no directories or files."""
    config = load_intake_sync_config(ROOT / "examples/intake/intake_config.json")
    result = run_intake_sync_with_records(
        config,
        _load("fake_rfis.json"),
        _load("fake_submittals.json"),
    )
    manifest = write_intake_sync_outputs(
        result,
        ROOT / "exports/intake-example",
        dry_run=True,
    )
    print(intake_to_json(manifest))


if __name__ == "__main__":
    main()
