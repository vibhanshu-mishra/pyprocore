"""Build and print a secret-free RFI/Submittal intake configuration."""

from pyprocore.intake import IntakeSyncConfig, intake_to_json


def main() -> None:
    """Print fake local intake configuration without calling Procore."""
    config = IntakeSyncConfig(
        profile_name="example-read-only",
        company_id=123456,
        project_ids=[1001],
        output_dir="./exports/intake",
        dry_run=True,
    )
    print(intake_to_json(config))


if __name__ == "__main__":
    main()
