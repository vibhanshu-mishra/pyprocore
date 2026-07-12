"""Tests for 2.1.0 post-release documentation state."""

from __future__ import annotations

import subprocess
import tomllib
import unittest
from pathlib import Path

import pyprocore

PROJECT_ROOT = Path(__file__).resolve().parents[1]


class VersionReleasePrepTestCase(unittest.TestCase):
    """Validate 2.1.0 released version and docs state."""

    def read_text(self, relative_path: str) -> str:
        """Read a repository file.

        Args:
            relative_path: Path relative to the project root.
        """
        return (PROJECT_ROOT / relative_path).read_text(encoding="utf-8")

    def test_package_version_is_2_1_0(self) -> None:
        """The package root should expose the prepared release version."""
        self.assertEqual(pyprocore.__version__, "2.1.0")

    def test_pyproject_version_is_2_1_0(self) -> None:
        """pyproject metadata should match the package root version."""
        pyproject = tomllib.loads(self.read_text("pyproject.toml"))

        self.assertEqual(pyproject["project"]["version"], "2.1.0")

    def test_changelog_has_2_1_0_section(self) -> None:
        """CHANGELOG should have a dated 2.1.0 release section."""
        changelog = self.read_text("CHANGELOG.md")

        self.assertIn("## [Unreleased]", changelog)
        self.assertIn("No unreleased changes yet.", changelog)
        self.assertIn("## [2.1.0] - 2026-07-11", changelog)
        self.assertIn("expanded API coverage", changelog)
        self.assertIn("Release-candidate validation tooling", changelog)

    def test_docs_mention_2_1_0_released_state(self) -> None:
        """Release docs should identify 2.1.0 as published and released."""
        release_doc = self.read_text("docs/release.md")
        readiness_doc = self.read_text("docs/final-release-readiness.md")
        readme = self.read_text("README.md")

        self.assertIn("PyProcore `2.1.0` has been published to PyPI", release_doc)
        self.assertIn("PyProcore `2.1.0` has been published to PyPI", readiness_doc)
        self.assertIn("Git tag `v2.1.0`", readiness_doc)
        self.assertIn("GitHub release", readiness_doc)
        self.assertIn("PyProcore `2.1.0` is available on PyPI", readme)

    def test_docs_do_not_claim_2_1_0_is_unpublished(self) -> None:
        """Docs should not keep stale 2.1.0 pre-publish language."""
        docs = "\n".join(
            [
                self.read_text("README.md"),
                self.read_text("docs/release.md"),
                self.read_text("docs/final-release-readiness.md"),
            ]
        )

        forbidden_phrases = (
            "PyPI publishing has not been performed for `2.1.0`",
            "No GitHub release has been created for `2.1.0`",
            "2.1.0 release candidate is prepared",
            "The prepared release candidate is `2.1.0`",
            "The next prepared release is `2.1.0`",
        )
        for phrase in forbidden_phrases:
            self.assertNotIn(phrase, docs)

        self.assertIn("PyPI publishing has been completed for `2.1.0`", docs)
        self.assertIn("Git tag `v2.1.0` was", docs)

    def test_github_workflow_files_are_unmodified(self) -> None:
        """Version prep should not modify GitHub Actions workflow files."""
        completed = subprocess.run(
            ["git", "diff", "--name-only", ".github/workflows"],
            cwd=PROJECT_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(completed.stdout.strip(), "")


if __name__ == "__main__":
    unittest.main()
