"""Print a concise Phase 10E async coverage summary."""

from __future__ import annotations


def main() -> None:
    """Print Phase 10E coverage notes."""
    print("Phase 10E expands read-only async coverage.")
    print("Included: financials, change-management, contracts, invoices, billing,")
    print("schedule metadata, tasks, calendar items, coordination issues, forms, and action plans.")
    print("Examples use mock data or dry-run plans and make no live Procore calls.")
    print("PyPI stable remains 2.2.0; Phase 10E is unreleased branch work until published later.")


if __name__ == "__main__":
    main()
