"""Summarize Phase 11B safe local plugin hook support.

This is a local overview example. It does not need Procore credentials and does
not run any external service.
"""

from __future__ import annotations

from pyprocore.plugins import PluginHookType, builtin_hook_registry


def main() -> None:
    """Print a short Phase 11B summary."""
    registry = builtin_hook_registry()
    print("Phase 11B: Safe Local Plugin Extension Hooks")
    print(f"Built-in hooks: {len(registry.list_hooks())}")
    print("Hook types:")
    for hook_type in PluginHookType:
        count = len(registry.find_hooks_by_type(hook_type))
        print(f"- {hook_type.value}: {count}")
    print("Mode: explicit local registration only.")


if __name__ == "__main__":
    main()
