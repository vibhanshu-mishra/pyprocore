"""Tests for release-readiness metadata and local checks."""

from __future__ import annotations

import subprocess
import sys
import tomllib
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


class ReleaseReadinessTestCase(unittest.TestCase):
    """Validate package metadata, release docs, and release-check tooling."""

    def test_release_check_script_exists_and_runs_locally(self) -> None:
        """The release checker runs without external services."""
        script = PROJECT_ROOT / "scripts" / "check_release_ready.py"
        self.assertTrue(script.exists())

        completed = subprocess.run(
            [sys.executable, str(script)],
            cwd=PROJECT_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertIn("Release readiness summary", completed.stdout)
        self.assertIn("PASS:", completed.stdout)

    def test_pyproject_metadata_contains_required_fields(self) -> None:
        """pyproject metadata is suitable for public package publication."""
        pyproject = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
        project = pyproject["project"]

        for field in [
            "name",
            "version",
            "description",
            "readme",
            "requires-python",
            "license",
            "authors",
            "maintainers",
            "keywords",
            "classifiers",
            "dependencies",
            "urls",
        ]:
            self.assertIn(field, project)
            self.assertTrue(project[field])

        self.assertEqual(project["name"], "pyprocore")
        self.assertEqual(project["readme"], "README.md")
        self.assertIn("Typing :: Typed", project["classifiers"])
        self.assertIn("Changelog", project["urls"])

    def test_readme_has_release_facing_sections(self) -> None:
        """README includes install, quick-start, examples, and security guidance."""
        readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")

        for heading in [
            "## Quick Start",
            "## What You Can Build",
            "## Supported Resource Families",
            "## CLI Overview",
            "## Safety Model",
            "## Documentation",
        ]:
            self.assertIn(heading, readme)
        self.assertIn("Never commit `.env`", readme)
        self.assertIn("docs/release.md", readme)

    def test_changelog_has_expected_unreleased_groups(self) -> None:
        """CHANGELOG keeps an unreleased section with grouped entries."""
        changelog = (PROJECT_ROOT / "CHANGELOG.md").read_text(encoding="utf-8")

        self.assertIn("## [Unreleased]", changelog)
        for heading in ["### Added", "### Changed", "### Fixed", "### Docs", "### Tests"]:
            self.assertIn(heading, changelog)
        self.assertIn("Phase 3 expanded API coverage", changelog)
        self.assertIn("Phase 4 AI-ready project intelligence", changelog)
        self.assertIn("Phase 5 automation foundation", changelog)
        self.assertIn("Phase 6 release readiness", changelog)

    def test_release_doc_exists(self) -> None:
        """Release documentation explains versioning and validation."""
        release_doc = (PROJECT_ROOT / "docs" / "release.md").read_text(encoding="utf-8")

        self.assertIn("Versioning", release_doc)
        self.assertIn("Pre-release Checklist", release_doc)
        self.assertIn("Publishing Checklist For Future Releases", release_doc)
        self.assertIn("make release-check", release_doc)

    def test_makefile_has_release_check_target(self) -> None:
        """Makefile exposes a combined release-check target."""
        makefile = (PROJECT_ROOT / "Makefile").read_text(encoding="utf-8")

        self.assertIn("release-check:", makefile)
        self.assertIn("scripts/check_release_ready.py", makefile)
        self.assertIn("$(MAKE) examples-check", makefile)
        self.assertIn("$(MAKE) typecheck", makefile)

    def test_secret_patterns_are_ignored_for_git_and_docker(self) -> None:
        """Git and Docker ignore rules cover secrets and generated outputs."""
        gitignore = (PROJECT_ROOT / ".gitignore").read_text(encoding="utf-8")
        dockerignore = (PROJECT_ROOT / ".dockerignore").read_text(encoding="utf-8")

        for pattern in [
            ".env",
            "token_store.json",
            "pyprocore/auth/token_store.json",
            "downloads",
            "logs",
            "pyprocore-runs",
            "webhook-events",
        ]:
            self.assertIn(pattern, gitignore)
            self.assertIn(pattern, dockerignore)

    def test_manifest_includes_docs_examples_and_excludes_sensitive_outputs(self) -> None:
        """Source distribution manifest includes useful docs and excludes secrets."""
        manifest = (PROJECT_ROOT / "MANIFEST.in").read_text(encoding="utf-8")

        self.assertIn("recursive-include docs *.md", manifest)
        self.assertIn("recursive-include examples", manifest)
        self.assertIn("exclude .env", manifest)
        self.assertIn("exclude pyprocore/auth/token_store.json", manifest)
        self.assertIn("recursive-exclude downloads *", manifest)


if __name__ == "__main__":
    unittest.main()
