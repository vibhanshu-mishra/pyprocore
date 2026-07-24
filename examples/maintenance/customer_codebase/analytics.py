"""Fake local analytics reference used by maintenance examples."""

from pyprocore.analytics import run_rfi_aging_recipe


def analyze_export() -> object:
    """Show a local analytics helper reference without running it."""
    return run_rfi_aging_recipe("exports/rfis.json")
