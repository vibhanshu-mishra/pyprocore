"""Fake dynamic access that the scanner must classify conservatively."""

from pyprocore import Procore


def find_service(service_name: str) -> object:
    """Show unresolved dynamic access without executing it during scans."""
    client = Procore()
    return getattr(client, service_name)
