"""Demonstrate redaction in local scanner report snippets."""

from pathlib import Path

from pyprocore.maintenance import scan_pyprocore_usage

EXAMPLES_DIR = Path(__file__).resolve().parent
FAKE_CODEBASE = EXAMPLES_DIR / "maintenance" / "customer_codebase"


def main() -> None:
    """Print only already-redacted snippets from the scan report."""
    report = scan_pyprocore_usage(FAKE_CODEBASE)
    snippets = [usage.snippet for usage in report.usages if usage.snippet]
    redacted = [snippet for snippet in snippets if "[REDACTED]" in snippet]
    print(f"Redacted snippets found: {len(redacted)}")
    for snippet in redacted:
        print(snippet)


if __name__ == "__main__":
    main()
