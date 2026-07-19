"""Evaluate metadata-only plugin artifacts.

The evals inspect JSON-like plugin metadata only. They do not install, load, or
execute plugins.
"""

from pyprocore.evals import run_builtin_eval_suites


def main() -> None:
    """Run plugin manifest and plugin config eval suites."""
    manifest = run_builtin_eval_suites(suite="golden_plugin_manifest_basic")
    config = run_builtin_eval_suites(suite="golden_plugin_config_basic")
    print(f"Plugin manifest eval passed: {manifest.passed}")
    print(f"Plugin config eval passed: {config.passed}")
    print("Plugin execution stayed disabled.")


if __name__ == "__main__":
    main()
