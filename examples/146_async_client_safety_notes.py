"""Print Phase 10A async client safety notes.

This example is intentionally documentation-like. It does not import optional
HTTP clients, call Procore, call AI/model APIs, or execute agent tools.
"""

from __future__ import annotations


def main() -> None:
    """Print the Phase 10A async safety boundaries."""
    print("Phase 10A async client safety notes:")
    print("- Existing sync Procore client remains supported.")
    print("- AsyncProcore is additive and read-oriented.")
    print("- MockAsyncTransport can test workflows without live Procore calls.")
    print("- Real async HTTP requires the optional pyprocore[async] extra.")
    print("- No create/update/delete helpers are added in Phase 10A.")
    print("- Agent tool execution remains disabled.")
    print("- MCP remains discovery-only.")


if __name__ == "__main__":
    main()
