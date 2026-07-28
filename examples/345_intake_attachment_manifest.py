"""Build an attachment download manifest from fake local records."""

import json
from pathlib import Path
from typing import Literal, cast

from pyprocore.intake import (
    build_intake_attachment_manifest,
    render_attachment_manifest_markdown,
)

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    """Inspect attachment metadata without following remote URLs."""
    payload = json.loads(
        (ROOT / "examples/intake/fake_attachment_records.json").read_text(encoding="utf-8")
    )
    records = [
        (
            cast(Literal["rfi", "submittal"], item["resource"]),
            int(item["project_id"]),
            item["record"],
        )
        for item in payload
    ]
    print(render_attachment_manifest_markdown(build_intake_attachment_manifest(records)))


if __name__ == "__main__":
    main()
