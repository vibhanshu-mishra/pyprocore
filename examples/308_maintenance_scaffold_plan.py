"""Plan draft files for a safe endpoint in a fake local OAS file."""

from pathlib import Path

from pyprocore.maintenance import (
    plan_read_only_endpoint_scaffold,
    scaffold_plan_to_markdown,
)

OAS_PATH = Path(__file__).resolve().parent / "maintenance" / "new_fake_procore_oas.json"
ENDPOINT_PATH = "/rest/v1.0/projects/{project_id}/readiness_checks"


def main() -> None:
    """Print a draft scaffold plan without writing files."""
    plan = plan_read_only_endpoint_scaffold(OAS_PATH, ENDPOINT_PATH)
    print(scaffold_plan_to_markdown(plan))


if __name__ == "__main__":
    main()
