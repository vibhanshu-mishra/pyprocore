"""Export the safe built-in plugin registry manifest to a temporary file.

The export is local metadata only. It does not install plugins, execute plugin
code, or call Procore.
"""

import json
import tempfile
from pathlib import Path

from pyprocore.plugins import PluginRegistry, discover_builtin_plugins


def main() -> None:
    """Write a plugin registry manifest JSON file in a temporary directory."""
    registry = PluginRegistry(discover_builtin_plugins().discovered)
    manifest = registry.export_plugin_registry_manifest()

    with tempfile.TemporaryDirectory() as directory:
        output_path = Path(directory) / "plugin-registry.json"
        output_path.write_text(
            json.dumps(manifest.model_dump(mode="json"), indent=2),
            encoding="utf-8",
        )
        print(f"Wrote local metadata manifest: {output_path}")
        print(f"Plugins: {manifest.plugin_count}")


if __name__ == "__main__":
    main()
