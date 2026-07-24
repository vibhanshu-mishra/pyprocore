"""Tests for prepared 2.4.0 release documentation state."""

from __future__ import annotations

import subprocess
import tomllib
import unittest
from pathlib import Path

import pyprocore

PROJECT_ROOT = Path(__file__).resolve().parents[1]


class VersionReleasePrepTestCase(unittest.TestCase):
    """Validate prepared 2.4.0 metadata and published 2.3.0 history."""

    def read_text(self, relative_path: str) -> str:
        """Read a repository file.

        Args:
            relative_path: Path relative to the project root.
        """
        return (PROJECT_ROOT / relative_path).read_text(encoding="utf-8")

    def test_package_version_is_2_4_0(self) -> None:
        """The package root should expose the prepared version."""
        self.assertEqual(pyprocore.__version__, "2.4.0")

    def test_pyproject_version_is_2_4_0(self) -> None:
        """pyproject metadata should match the package root version."""
        pyproject = tomllib.loads(self.read_text("pyproject.toml"))

        self.assertEqual(pyproject["project"]["version"], "2.4.0")

    def test_changelog_has_2_4_0_release_section(self) -> None:
        """CHANGELOG should have dated 2.4.0 and historical 2.3.0 sections."""
        changelog = self.read_text("CHANGELOG.md")

        self.assertIn("## [Unreleased]", changelog)
        self.assertIn("## [2.4.0] - 2026-07-24", changelog)
        self.assertIn("## [2.3.0] - 2026-07-19", changelog)
        self.assertIn("Phase 8A read-only API coverage", changelog)
        self.assertIn("Phase 15C MCP compatibility polish", changelog)
        self.assertIn("## [2.2.0] - 2026-07-12", changelog)

    def test_docs_mention_2_3_0_released_state(self) -> None:
        """Release docs should identify 2.3.0 as published and released."""
        docs = "\n".join(
            [
                self.read_text("README.md"),
                self.read_text("docs/release.md"),
                self.read_text("docs/project-status.md"),
            ]
        )

        self.assertIn("Current stable release: `2.3.0`", docs)
        self.assertIn("PyProcore `2.3.0` has been published to PyPI", docs)
        self.assertIn("tagged as `v2.3.0`", docs)
        self.assertIn("released on GitHub", docs)
        self.assertIn("Previous stable release: `2.2.0`", docs)
        self.assertIn("Prepared package version: `2.4.0`", docs)
        self.assertIn("not yet been published", docs)

    def test_docs_do_not_claim_2_3_0_is_unpublished(self) -> None:
        """Docs should not keep stale 2.3.0 pre-publish language."""
        docs = "\n".join(
            [
                self.read_text("README.md"),
                self.read_text("docs/release.md"),
                self.read_text("docs/project-status.md"),
            ]
        )

        forbidden_phrases = (
            "2.3.0 has not been published",
            "2.3.0 is prepared",
            "prepared next release",
            "The prepared release candidate is `2.3.0`",
            "publish 2.3.0 later",
        )
        for phrase in forbidden_phrases:
            self.assertNotIn(phrase, docs)

    def test_docs_do_not_claim_2_4_0_is_published(self) -> None:
        """Prepared release docs must not claim publication or release completion."""
        docs = "\n".join(
            [
                self.read_text("README.md"),
                self.read_text("docs/release.md"),
                self.read_text("docs/project-status.md"),
                self.read_text("docs/index.md"),
            ]
        )

        for phrase in (
            "2.4.0 has been published",
            "2.4.0 is published",
            "tagged as `v2.4.0`",
            "`v2.4.0` GitHub release created",
        ):
            self.assertNotIn(phrase, docs)

    def test_github_workflow_files_are_unmodified(self) -> None:
        """Version docs cleanup should not modify GitHub Actions workflow files."""
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
