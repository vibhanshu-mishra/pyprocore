"""Fake customer workflow references used by local maintenance examples."""

from pyprocore import build_project_context_package


def build_context() -> object:
    """Show a workflow helper reference without running it during scans."""
    return build_project_context_package(project_id=123)
