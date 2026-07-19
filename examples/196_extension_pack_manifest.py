"""Create a safe local extension-pack manifest template.

Extension packs are metadata bundles only. They do not install packages, import
modules, register hook callables, or execute hooks.
"""

from __future__ import annotations

from pyprocore.plugins import export_extension_pack_template


def main() -> None:
    """Print extension-pack template details."""
    extension_pack = export_extension_pack_template()

    print("Extension-pack template")
    print(f"Name: {extension_pack.name}")
    print(f"Included plugins: {len(extension_pack.included_plugins)}")
    print(f"Included hooks: {len(extension_pack.included_hooks)}")
    print("Mode: metadata only.")


if __name__ == "__main__":
    main()
