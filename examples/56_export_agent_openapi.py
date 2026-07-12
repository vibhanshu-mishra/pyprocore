"""Export the local PyProcore Agent API OpenAPI document.

This example does not require Procore credentials, does not read `.env`, and
does not call the Procore API. It writes a machine-readable OpenAPI file that
agent frameworks, gateways, and documentation tools can inspect.
"""

from __future__ import annotations

from pathlib import Path

from pyprocore.agent import export_agent_openapi_json


def main() -> None:
    """Write the OpenAPI document to a local examples output folder."""
    output_dir = Path("exports/examples/agent")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "agent-openapi.json"

    output_path.write_text(export_agent_openapi_json(pretty=True), encoding="utf-8")

    print("Agent OpenAPI document exported.")
    print(f"Output: {output_path}")
    print("No Procore credentials were required and no live API calls were made.")


if __name__ == "__main__":
    main()
