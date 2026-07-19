"""List PyProcore's built-in safe local hooks.

Built-in hooks are deterministic helpers for validation, formatting, local
exports, and reports. They do not make Procore or AI calls.
"""

from __future__ import annotations

from pyprocore.plugins import builtin_hook_registry


def main() -> None:
    """Print built-in hook metadata."""
    registry = builtin_hook_registry()
    print(f"Built-in hooks: {len(registry.list_hooks())}")
    for hook in registry.list_hooks():
        print(f"- {hook.hook_name} ({hook.hook_type.value})")


if __name__ == "__main__":
    main()
