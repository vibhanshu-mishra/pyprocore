"""Render placeholder-only GC/Owner onboarding email templates."""

from pyprocore.dmsa import (
    build_gc_owner_email_templates,
    gc_owner_email_templates_to_markdown,
)


def main() -> None:
    """Print copy-ready local templates for human review."""
    print(gc_owner_email_templates_to_markdown(build_gc_owner_email_templates()))


if __name__ == "__main__":
    main()
