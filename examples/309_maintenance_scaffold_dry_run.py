"""Dry-run a draft read-only scaffold copy using only fake local metadata."""

import tempfile
from pathlib import Path

from pyprocore.maintenance import (
    copy_read_only_endpoint_scaffold,
    plan_read_only_endpoint_scaffold,
    scaffold_copy_result_to_markdown,
)

OAS_PATH = Path(__file__).resolve().parent / "maintenance" / "new_fake_procore_oas.json"
ENDPOINT_PATH = "/rest/v1.0/projects/{project_id}/readiness_checks"


def main() -> None:
    """Validate draft destinations without writing any files."""
    plan = plan_read_only_endpoint_scaffold(OAS_PATH, ENDPOINT_PATH)
    with tempfile.TemporaryDirectory() as temp_dir:
        result = copy_read_only_endpoint_scaffold(
            plan,
            Path(temp_dir) / "draft",
            dry_run=True,
        )
        print(scaffold_copy_result_to_markdown(result))


if __name__ == "__main__":
    main()
