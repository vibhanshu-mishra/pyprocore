"""Build and print a secret-free DMSA connection profile locally."""

from pyprocore.dmsa import build_dmsa_connection_profile, dmsa_report_to_json


def main() -> None:
    """Print fake profile metadata without reading credentials or calling Procore."""
    profile = build_dmsa_connection_profile(
        profile_name="example-read-only",
        company_id=123456,
        allowed_project_ids=[1001],
        created_for="Example subcontractor",
    )
    print(dmsa_report_to_json(profile))


if __name__ == "__main__":
    main()
