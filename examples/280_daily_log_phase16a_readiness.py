"""Show Daily Logs read-only coverage and deferred ambiguous log types.

This example is local-only. It helps users understand which Daily Log helpers
already have clear endpoint patterns in PyProcore and which requested log
families remain deferred until a safe documented GET path is confirmed.
"""

from pyprocore.services.daily_logs import DAILY_LOG_TYPES

DEFERRED_LOG_TYPES = (
    "weather logs",
    "equipment logs",
    "waste logs beyond the existing dumpster-log helper",
)


def main() -> None:
    """Print Daily Logs coverage notes without calling Procore."""
    print("Daily Logs read-only helpers currently available:")
    for log_type in DAILY_LOG_TYPES:
        print(f"- {log_type}")

    print("\nDeferred until safe endpoint shape is confirmed:")
    for log_type in DEFERRED_LOG_TYPES:
        print(f"- {log_type}")

    print("\nNo live Procore calls were made.")


if __name__ == "__main__":
    main()
