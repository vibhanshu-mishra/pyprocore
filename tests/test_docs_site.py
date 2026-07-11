"""Tests for the MkDocs documentation site skeleton."""

from __future__ import annotations

import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


class DocsSiteTests(unittest.TestCase):
    """Verify the documentation site structure stays complete."""

    def read_text(self, relative_path: str) -> str:
        """Read a repository file as UTF-8 text.

        Args:
            relative_path: Path relative to the repository root.

        Returns:
            File contents.
        """
        return (PROJECT_ROOT / relative_path).read_text(encoding="utf-8")

    def test_mkdocs_config_exists_and_references_key_pages(self) -> None:
        """MkDocs should have a simple config and nav for primary docs pages."""
        mkdocs_path = PROJECT_ROOT / "mkdocs.yml"

        self.assertTrue(mkdocs_path.exists())
        mkdocs = self.read_text("mkdocs.yml")

        self.assertIn("site_name: PyProcore", mkdocs)
        self.assertIn("repo_url: https://github.com/vibhanshu-mishra/pyprocore", mkdocs)
        self.assertIn("theme:", mkdocs)
        self.assertIn("readthedocs", mkdocs)

        for nav_entry in (
            "index.md",
            "getting-started.md",
            "authentication.md",
            "cli.md",
            "api-coverage.md",
            "workflows.md",
            "ai-review.md",
            "automation.md",
            "recipes/index.md",
            "contributing.md",
            "release.md",
            "changelog.md",
        ):
            self.assertIn(nav_entry, mkdocs)

    def test_key_docs_pages_exist(self) -> None:
        """The docs site should include the Phase 6C landing pages."""
        for relative_path in (
            "docs/index.md",
            "docs/getting-started.md",
            "docs/authentication.md",
            "docs/cli.md",
            "docs/api-coverage.md",
            "docs/workflows.md",
            "docs/ai-review.md",
            "docs/automation.md",
            "docs/recipes/index.md",
            "docs/contributing.md",
            "docs/changelog.md",
        ):
            self.assertTrue((PROJECT_ROOT / relative_path).exists(), relative_path)

    def test_docs_homepage_is_beginner_safe(self) -> None:
        """Homepage should identify the project and include safety guidance."""
        homepage = self.read_text("docs/index.md")

        self.assertIn("PyProcore", homepage)
        self.assertIn("Procore REST API", homepage)
        self.assertIn("read-oriented", homepage)
        self.assertIn("not affiliated", homepage)
        self.assertIn("Never commit", homepage)

    def test_recipe_index_links_existing_recipe_categories(self) -> None:
        """Recipes index should organize existing task-based docs."""
        recipes = self.read_text("docs/recipes/index.md")

        for heading in (
            "Auth And Setup",
            "RFIs",
            "Submittals",
            "Documents",
            "Drawings",
            "Specifications",
            "Photos",
            "Daily Logs",
            "Project Context And AI Review",
            "Workflow Plans And Automation",
            "Webhooks",
        ):
            self.assertIn(heading, recipes)

    def test_readme_mentions_documentation_site(self) -> None:
        """README should point users to the docs site entry point."""
        readme = self.read_text("README.md")

        self.assertIn("## Documentation Site", readme)
        self.assertIn("docs/index.md", readme)
        self.assertIn("make docs-serve", readme)
        self.assertIn("make docs-build", readme)

    def test_pyproject_has_docs_optional_dependency(self) -> None:
        """MkDocs should be optional and not part of runtime dependencies."""
        pyproject = self.read_text("pyproject.toml")

        self.assertIn("[project.optional-dependencies]", pyproject)
        self.assertIn("docs = [", pyproject)
        self.assertIn('"mkdocs>=1.5"', pyproject)

    def test_makefile_has_docs_targets(self) -> None:
        """Makefile should expose local docs preview and strict build targets."""
        makefile = self.read_text("Makefile")

        self.assertIn("docs-serve:", makefile)
        self.assertIn("mkdocs serve", makefile)
        self.assertIn("docs-build:", makefile)
        self.assertIn("mkdocs build --strict", makefile)


if __name__ == "__main__":
    unittest.main()
