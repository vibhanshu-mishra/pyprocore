"""Show Phase 16B plugin trust safety boundaries.

The trust layer is metadata-only. It validates local JSON policy and manifest
files but never installs, fetches, imports, or executes plugins.
"""

from __future__ import annotations

BOUNDARIES = [
    "Trust policy files are JSON-only and local.",
    "Remote plugin installation is denied by default.",
    "Execution from manifests and configs is denied by default.",
    "Arbitrary imports are denied by default.",
    "Signature/checksum fields are metadata unless explicit local verification is added.",
    "MCP remains discovery-only.",
    "Procore tool execution remains disabled.",
]


def main() -> None:
    """Print the local-only trust boundaries."""
    print("PyProcore Phase 16B plugin trust boundaries:")
    for boundary in BOUNDARIES:
        print(f"- {boundary}")


if __name__ == "__main__":
    main()
