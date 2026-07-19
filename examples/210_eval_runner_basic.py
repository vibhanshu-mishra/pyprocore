"""Run all built-in deterministic golden eval suites locally.

The runner evaluates bundled placeholder artifacts only. It does not call
Procore, execute tools, execute plugins, or call external AI/model APIs.
"""

from pyprocore.evals import run_builtin_eval_suites


def main() -> None:
    """Run built-in golden evals and print a compact result."""
    report = run_builtin_eval_suites()
    print(f"Suites passed: {report.passed_suites}/{report.total_suites}")
    print(f"Cases passed: {report.passed_cases}/{report.total_cases}")
    print(f"Score: {report.score}/{report.max_score}")


if __name__ == "__main__":
    main()
