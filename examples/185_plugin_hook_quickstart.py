"""Register and run a trusted local PyProcore plugin hook.

This example uses an in-process callable that you pass directly to the hook
registry. It does not import plugins by path, install packages, call Procore, or
use credentials.
"""

from __future__ import annotations

from typing import Any

from pyprocore.plugins import (
    PluginHookContext,
    PluginHookMetadata,
    PluginHookRegistry,
    PluginHookType,
)


def count_records(_context: PluginHookContext, payload: Any) -> dict[str, int]:
    """Return a tiny local summary for sample records."""
    records = payload if isinstance(payload, list) else []
    return {"record_count": len(records)}


def main() -> None:
    """Run the hook quickstart."""
    registry = PluginHookRegistry()
    registry.register_hook(
        PluginHookMetadata(
            hook_name="count_records",
            plugin_name="local_examples",
            hook_type=PluginHookType.REPORT,
            description="Count local records.",
            output_kind="report",
        ),
        count_records,
    )

    result = registry.run_hook(
        "count_records",
        [{"id": 1, "name": "Sample RFI"}, {"id": 2, "name": "Sample Submittal"}],
    )
    print("Hook ran locally.")
    print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
