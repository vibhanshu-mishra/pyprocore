"""Print a suggested private PyProcore folder layout.

This example only prints text. It does not create folders or start schedules.
"""

from pyprocore.workflows import sample_private_folder_layout


def main() -> None:
    """Run the example."""
    print(sample_private_folder_layout("/opt/pyprocore"))


if __name__ == "__main__":
    main()
