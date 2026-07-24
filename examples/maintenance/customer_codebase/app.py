"""Fake customer application used only by local maintenance examples."""

from pyprocore import Procore


def list_open_rfis() -> object:
    """Show a static object-client call without making it during scans."""
    client = Procore()
    return client.rfis.list(project_id=123)
