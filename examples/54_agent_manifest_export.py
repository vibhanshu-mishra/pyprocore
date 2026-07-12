"""Export the PyProcore agent manifest to a local JSON file.

This example is safe to run without Procore credentials. It writes a local
manifest file under exports/ and never calls the Procore API.
"""

from pathlib import Path

from pyprocore.agent import export_agent_manifest_json


def main() -> None:
    """Write the agent manifest JSON to exports/agent_manifest.json."""
    output_path = Path("exports/agent_manifest.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(export_agent_manifest_json(pretty=True), encoding="utf-8")
    print("Agent manifest exported.")
    print(f"Output: {output_path}")


if __name__ == "__main__":
    main()
