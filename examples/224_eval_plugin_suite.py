"""Run local plugin metadata and config golden eval suites.

These suites inspect metadata-only plugin fixtures. They do not install,
fetch, import, or execute plugins.
"""

from pyprocore.evals import run_builtin_eval_suites


def main() -> None:
    """Run plugin-related eval suites one at a time."""
    for suite_name in ("plugin_metadata_golden", "plugin_config_golden"):
        report = run_builtin_eval_suites(suite=suite_name)
        print(f"{suite_name}: {report.status.value} ({report.score}/{report.max_score})")


if __name__ == "__main__":
    main()
