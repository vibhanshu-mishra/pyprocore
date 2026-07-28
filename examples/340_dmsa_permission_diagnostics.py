"""Interpret fake DMSA permission-response metadata locally."""

from pyprocore.dmsa import (
    diagnose_dmsa_permission_issue,
    dmsa_permission_diagnostic_to_markdown,
)


def main() -> None:
    """Print likely 403 causes without claiming certainty or calling Procore."""
    report = diagnose_dmsa_permission_issue(status_code=403, context="rfis")
    print(dmsa_permission_diagnostic_to_markdown(report))


if __name__ == "__main__":
    main()
