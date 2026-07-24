"""Build a human-review API maintenance plan from a fake local OAS file."""

from pathlib import Path

from pyprocore.maintenance import build_api_maintenance_plan, maintenance_plan_to_markdown

OAS_PATH = Path(__file__).resolve().parent / "maintenance" / "new_fake_procore_oas.json"


def main() -> None:
    """Print an advisory maintenance plan without modifying the SDK."""
    plan = build_api_maintenance_plan(OAS_PATH)
    print(maintenance_plan_to_markdown(plan))


if __name__ == "__main__":
    main()
