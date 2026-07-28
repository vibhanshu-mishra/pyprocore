"""Print the GC/Owner DMSA least-privilege permission checklist."""

from pyprocore.dmsa import (
    build_dmsa_permission_checklist,
    dmsa_permission_checklist_to_markdown,
)


def main() -> None:
    """Render a local checklist without credentials or Procore access."""
    print(dmsa_permission_checklist_to_markdown(build_dmsa_permission_checklist()))


if __name__ == "__main__":
    main()
