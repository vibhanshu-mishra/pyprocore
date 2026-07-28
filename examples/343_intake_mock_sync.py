"""Run RFI/Submittal intake against local fake JSON records."""

import json
from pathlib import Path

from pyprocore.intake import (
    intake_run_result_to_markdown,
    load_intake_sync_config,
    run_intake_sync_with_records,
)

ROOT = Path(__file__).resolve().parents[1]


def _load(name: str) -> dict[str, list[dict[str, object]]]:
    return json.loads((ROOT / f"examples/intake/{name}").read_text(encoding="utf-8"))


def main() -> None:
    """Run a deterministic local workflow without accessing credentials."""
    config = load_intake_sync_config(ROOT / "examples/intake/intake_config.json")
    result = run_intake_sync_with_records(
        config,
        _load("fake_rfis.json"),
        _load("fake_submittals.json"),
    )
    print(intake_run_result_to_markdown(result))


if __name__ == "__main__":
    main()
