"""Print safety notes for async exports and download patterns."""

from __future__ import annotations


def main() -> None:
    """Print beginner-friendly safety reminders."""
    print("PyProcore async export safety notes")
    print("- Async exports are read-only.")
    print("- Async download helpers only save files locally.")
    print("- No upload, create, update, or delete helpers are added by Phase 10B.")
    print("- Use pyprocore[async] only when you need the optional real async HTTP transport.")
    print("- Tests and examples use mock transports and do not call Procore.")


if __name__ == "__main__":
    main()
