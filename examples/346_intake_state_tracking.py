"""Load and display fake local polling state for repeated intake runs."""

from pathlib import Path

from pyprocore.intake import intake_state_to_markdown, load_intake_sync_state

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    """Display local state without credentials or Procore calls."""
    state = load_intake_sync_state(ROOT / "examples/intake/fake_state.json")
    print(intake_state_to_markdown(state))


if __name__ == "__main__":
    main()
