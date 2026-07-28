"""Render a least-privilege RFI/Submittal permission request."""

from pyprocore.dmsa import (
    build_rfi_submittal_permission_request,
    gc_owner_permission_request_to_markdown,
)


def main() -> None:
    """Print the local Read Only permission request."""
    print(gc_owner_permission_request_to_markdown(build_rfi_submittal_permission_request()))


if __name__ == "__main__":
    main()
