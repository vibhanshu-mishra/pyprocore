"""Explain sandbox and production credential separation for PyProcore."""

from __future__ import annotations

from pyprocore.auth.permissions import explain_sandbox_production_separation


def main() -> None:
    """Print environment separation guidance."""
    print("Sandbox and production separation")
    print(explain_sandbox_production_separation())
    print("Use separate .env files, token-store paths, and deployment secrets.")
    print("Never copy production tokens into sandbox examples or documentation.")


if __name__ == "__main__":
    main()
