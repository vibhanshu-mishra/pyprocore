"""Validate local release-candidate build artifacts without publishing."""

from __future__ import annotations

import argparse
import importlib.util
import os
import shutil
import subprocess
import sys
import tempfile
import venv
import zipfile
from dataclasses import dataclass
from email.parser import Parser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST_DIR = ROOT / "dist"
BUILD_DIR = ROOT / "build"
REQUIRED_IMPORTS = [
    "Procore",
    "build_project_context_package",
    "build_enhanced_rfi_package",
    "build_enhanced_submittal_package",
    "build_ai_review_export",
    "run_workflow_plan",
]


@dataclass(frozen=True)
class CheckResult:
    """Single release-candidate check result."""

    status: str
    message: str


class Reporter:
    """Collect and print release-candidate validation results."""

    def __init__(self) -> None:
        """Initialize an empty result collector."""
        self.results: list[CheckResult] = []

    def pass_(self, message: str) -> None:
        """Record a passing check.

        Args:
            message: Human-readable check message.
        """
        self._add("PASS", message)

    def warn(self, message: str) -> None:
        """Record a warning.

        Args:
            message: Human-readable warning message.
        """
        self._add("WARN", message)

    def fail(self, message: str) -> None:
        """Record a release-blocking failure.

        Args:
            message: Human-readable failure message.
        """
        self._add("FAIL", message)

    def _add(self, status: str, message: str) -> None:
        self.results.append(CheckResult(status=status, message=message))
        print(f"{status}: {message}")

    def has_failures(self) -> bool:
        """Return whether any release-blocking failures were recorded."""
        return any(result.status == "FAIL" for result in self.results)

    def has_warnings(self) -> bool:
        """Return whether any warnings were recorded."""
        return any(result.status == "WARN" for result in self.results)

    def print_summary(self) -> None:
        """Print a compact PASS/WARN/FAIL summary."""
        counts = {"PASS": 0, "WARN": 0, "FAIL": 0}
        for result in self.results:
            counts[result.status] += 1
        print(
            "Release candidate summary: "
            f"{counts['PASS']} passed, {counts['WARN']} warnings, {counts['FAIL']} failures."
        )


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Build, inspect, and locally install-check PyProcore release artifacts."
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat optional tooling warnings, such as missing twine, as failures.",
    )
    parser.add_argument(
        "--keep-artifacts",
        action="store_true",
        help="Keep dist/, build/, and egg-info artifacts after the check finishes.",
    )
    parser.add_argument(
        "--skip-build",
        action="store_true",
        help="Skip building and validate existing artifacts in dist/.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print command output from build, twine, and install checks.",
    )
    return parser.parse_args()


def clean_artifacts(reporter: Reporter) -> None:
    """Remove local build artifacts that are safe to regenerate.

    Args:
        reporter: Result collector used for user-facing status messages.
    """
    for path in [DIST_DIR, BUILD_DIR, *ROOT.glob("*.egg-info")]:
        if path.exists():
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()
            reporter.pass_(f"Removed previous build artifact: {path.relative_to(ROOT)}")


def module_is_available(module_name: str) -> bool:
    """Return whether a Python module can be imported in the current interpreter.

    Args:
        module_name: Module name to check.
    """
    return importlib.util.find_spec(module_name) is not None


def run_command(
    command: list[str],
    reporter: Reporter,
    failure_message: str,
    *,
    env: dict[str, str] | None = None,
    verbose: bool = False,
    record_failure: bool = True,
) -> bool:
    """Run a command and record a failure if it exits nonzero.

    Args:
        command: Command and arguments to run.
        reporter: Result collector used for status messages.
        failure_message: Message to record on nonzero exit.
        env: Optional environment variables.
        verbose: Whether to print command output.
        record_failure: Whether to record a failed command as a release-blocking failure.

    Returns:
        True when the command succeeds, otherwise False.
    """
    completed = subprocess.run(
        command,
        cwd=ROOT,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    if verbose and completed.stdout:
        print(completed.stdout)
    if completed.returncode != 0:
        details = completed.stdout.strip()
        if record_failure:
            if details:
                reporter.fail(f"{failure_message}\n{details}")
            else:
                reporter.fail(failure_message)
        return False
    return True


def build_package(reporter: Reporter, verbose: bool) -> bool:
    """Build the source distribution and wheel.

    Args:
        reporter: Result collector used for status messages.
        verbose: Whether to print build command output.

    Returns:
        True if build artifacts were created successfully.
    """
    if not module_is_available("build"):
        reporter.fail(
            "Package build tool is missing. Install it with: python3 -m pip install build"
        )
        return False

    if run_command(
        [sys.executable, "-m", "build"],
        reporter,
        "Failed to build release artifacts with python3 -m build.",
        verbose=verbose,
        record_failure=False,
    ):
        reporter.pass_("Built source distribution and wheel.")
        return True

    reporter.warn(
        "Isolated build failed. This can happen in offline environments when build "
        "dependencies cannot be fetched from PyPI. Retrying with --no-isolation."
    )
    if run_command(
        [sys.executable, "-m", "build", "--no-isolation"],
        reporter,
        "Failed to build release artifacts with python3 -m build --no-isolation.",
        verbose=verbose,
    ):
        reporter.pass_("Built source distribution and wheel without build isolation.")
        return True
    return False


def find_artifacts(reporter: Reporter) -> tuple[Path | None, Path | None]:
    """Find built source distribution and wheel artifacts.

    Args:
        reporter: Result collector used for status messages.

    Returns:
        Tuple of source distribution path and wheel path when present.
    """
    source_distributions = sorted(DIST_DIR.glob("*.tar.gz"))
    wheels = sorted(DIST_DIR.glob("*.whl"))

    source_distribution = source_distributions[-1] if source_distributions else None
    wheel = wheels[-1] if wheels else None

    if source_distribution is None:
        reporter.fail("No source distribution found in dist/. Expected a .tar.gz file.")
    else:
        reporter.pass_(f"Found source distribution: {source_distribution.name}")

    if wheel is None:
        reporter.fail("No wheel found in dist/. Expected a .whl file.")
    else:
        reporter.pass_(f"Found wheel: {wheel.name}")

    return source_distribution, wheel


def inspect_wheel_metadata(wheel: Path, reporter: Reporter) -> None:
    """Inspect package metadata from the built wheel.

    Args:
        wheel: Wheel artifact path.
        reporter: Result collector used for status messages.
    """
    with zipfile.ZipFile(wheel) as archive:
        metadata_names = [
            name for name in archive.namelist() if name.endswith(".dist-info/METADATA")
        ]
        if not metadata_names:
            reporter.fail("Wheel metadata file was not found.")
            return
        metadata_text = archive.read(metadata_names[0]).decode("utf-8")

    metadata = Parser().parsestr(metadata_text)
    required_fields = {
        "Name": metadata.get("Name"),
        "Version": metadata.get("Version"),
        "Summary": metadata.get("Summary"),
        "Requires-Python": metadata.get("Requires-Python"),
        "License": metadata.get("License") or metadata.get("License-File"),
    }

    missing = [name for name, value in required_fields.items() if not value]
    if missing:
        reporter.fail(f"Wheel metadata is missing required fields: {', '.join(missing)}")
    else:
        reporter.pass_(
            "Wheel metadata present: "
            f"name={required_fields['Name']}, "
            f"version={required_fields['Version']}, "
            f"requires-python={required_fields['Requires-Python']}"
        )

    dependencies = metadata.get_all("Requires-Dist") or []
    if dependencies:
        reporter.pass_(f"Wheel metadata lists {len(dependencies)} dependencies.")
    else:
        reporter.fail("Wheel metadata does not list runtime dependencies.")


def run_twine_check(reporter: Reporter, strict: bool, verbose: bool) -> None:
    """Run twine artifact validation when twine is installed.

    Args:
        reporter: Result collector used for status messages.
        strict: Whether missing twine should fail the check.
        verbose: Whether to print twine command output.
    """
    if not module_is_available("twine"):
        message = "twine is not installed. Install it with: python3 -m pip install twine"
        if strict:
            reporter.fail(message)
        else:
            reporter.warn(f"{message} Skipping twine check.")
        return

    artifacts = [str(path) for path in sorted(DIST_DIR.iterdir()) if path.is_file()]
    if run_command(
        [sys.executable, "-m", "twine", "check", *artifacts],
        reporter,
        "twine metadata validation failed.",
        verbose=verbose,
    ):
        reporter.pass_("twine metadata validation passed.")


def virtualenv_paths(venv_dir: Path) -> tuple[Path, Path]:
    """Return Python and console-script paths for a temporary virtual environment.

    Args:
        venv_dir: Virtual environment directory.
    """
    if os.name == "nt":
        return venv_dir / "Scripts" / "python.exe", venv_dir / "Scripts" / "procore-sdk.exe"
    return venv_dir / "bin" / "python", venv_dir / "bin" / "procore-sdk"


def verify_wheel_install(wheel: Path, reporter: Reporter, verbose: bool) -> None:
    """Install the wheel into a temporary virtual environment and smoke-check it.

    Args:
        wheel: Wheel artifact path.
        reporter: Result collector used for status messages.
        verbose: Whether to print install and smoke-check output.
    """
    with tempfile.TemporaryDirectory(prefix="pyprocore-rc-") as temp_dir:
        venv_dir = Path(temp_dir) / ".venv-release"
        venv.EnvBuilder(with_pip=True).create(venv_dir)
        python_path, cli_path = virtualenv_paths(venv_dir)

        installed_cleanly = run_command(
            [str(python_path), "-m", "pip", "install", str(wheel)],
            reporter,
            "Failed to install built wheel in a clean temporary environment.",
            verbose=verbose,
            record_failure=False,
        )
        if installed_cleanly:
            reporter.pass_("Installed wheel in a clean temporary environment.")
        else:
            reporter.warn(
                "Clean wheel install could not resolve dependencies. This can happen "
                "offline. Retrying wheel install with local site packages and --no-deps."
            )
            venv_dir = Path(temp_dir) / ".venv-release-local-deps"
            venv.EnvBuilder(with_pip=True, system_site_packages=True).create(venv_dir)
            python_path, cli_path = virtualenv_paths(venv_dir)
            if not run_command(
                [str(python_path), "-m", "pip", "install", "--no-deps", str(wheel)],
                reporter,
                "Failed to install built wheel with local dependency fallback.",
                verbose=verbose,
            ):
                return
            reporter.pass_("Installed wheel with local dependency fallback.")

        version_command = "import pyprocore; print(pyprocore.__version__)"
        if run_command(
            [str(python_path), "-c", version_command],
            reporter,
            "Installed package could not import pyprocore.__version__.",
            verbose=verbose,
        ):
            reporter.pass_("Verified pyprocore package import and __version__ export.")

        import_command = (
            "import pyprocore; "
            f"missing = [name for name in {REQUIRED_IMPORTS!r} if not hasattr(pyprocore, name)]; "
            "raise SystemExit('Missing exports: ' + ', '.join(missing) if missing else 0)"
        )
        if run_command(
            [str(python_path), "-c", import_command],
            reporter,
            "Installed package is missing required public exports.",
            verbose=verbose,
        ):
            reporter.pass_("Verified important pyprocore public exports.")

        if run_command(
            [str(cli_path), "--help"],
            reporter,
            "Installed procore-sdk console script failed to run --help.",
            verbose=verbose,
        ):
            reporter.pass_("Verified installed procore-sdk CLI help.")


def main() -> int:
    """Run release-candidate validation.

    Returns:
        Process exit code.
    """
    args = parse_args()
    reporter = Reporter()

    if not args.skip_build:
        clean_artifacts(reporter)
        build_package(reporter, verbose=args.verbose)
    else:
        reporter.warn("Skipping package build and validating existing dist/ artifacts.")

    _, wheel = find_artifacts(reporter)
    if wheel is not None:
        inspect_wheel_metadata(wheel, reporter)
        run_twine_check(reporter, strict=args.strict, verbose=args.verbose)
        verify_wheel_install(wheel, reporter, verbose=args.verbose)

    if not args.keep_artifacts:
        clean_artifacts(reporter)
        reporter.pass_("Cleaned release artifacts after validation.")
    else:
        reporter.warn("Keeping release artifacts because --keep-artifacts was provided.")

    reporter.print_summary()
    return 1 if reporter.has_failures() else 0


if __name__ == "__main__":
    raise SystemExit(main())
