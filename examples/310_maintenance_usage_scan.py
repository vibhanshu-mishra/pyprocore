"""Scan the bundled fake customer codebase for local PyProcore usage."""

from pathlib import Path

from pyprocore.maintenance import scan_pyprocore_usage

EXAMPLES_DIR = Path(__file__).resolve().parent
FAKE_CODEBASE = EXAMPLES_DIR / "maintenance" / "customer_codebase"


def main() -> None:
    """Print a local-only usage scan summary."""
    report = scan_pyprocore_usage(FAKE_CODEBASE)
    print(f"Scanned {len(report.files_scanned)} local files.")
    print(f"Found {len(report.usages)} PyProcore usage rows.")
    print("No files were executed or modified.")


if __name__ == "__main__":
    main()
