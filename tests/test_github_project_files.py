"""Tests for GitHub project/community repository files."""

from __future__ import annotations

import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


class GitHubProjectFilesTestCase(unittest.TestCase):
    """Validate GitHub/community polish files without calling GitHub."""

    def test_community_docs_exist(self) -> None:
        """Contributor, conduct, security, and support docs are present."""
        for relative_path in [
            "CONTRIBUTING.md",
            "CODE_OF_CONDUCT.md",
            "SECURITY.md",
            "SUPPORT.md",
        ]:
            self.assertTrue((PROJECT_ROOT / relative_path).exists(), relative_path)

    def test_contributing_doc_has_practical_guidance(self) -> None:
        """Contributing docs explain local setup, checks, endpoints, and secrets."""
        text = (PROJECT_ROOT / "CONTRIBUTING.md").read_text(encoding="utf-8")

        for expected in [
            "python3 -m pip install -e",
            "make examples-check",
            "make test",
            "make lint",
            "make typecheck",
            "Adding a New Endpoint",
            "Secret Safety",
            "Opening a Pull Request",
        ]:
            self.assertIn(expected, text)
        self.assertIn("Do not commit", text)

    def test_security_and_support_docs_warn_about_secrets(self) -> None:
        """Security/support docs tell users not to disclose credentials."""
        combined = "\n".join(
            [
                (PROJECT_ROOT / "SECURITY.md").read_text(encoding="utf-8"),
                (PROJECT_ROOT / "SUPPORT.md").read_text(encoding="utf-8"),
            ]
        )

        for expected in [
            "do not open public GitHub issues",
            "client secrets",
            "access tokens",
            "refresh tokens",
            "token store",
            "Authorization headers",
            "not official Procore support",
        ]:
            self.assertIn(expected, combined)

    def test_issue_templates_exist(self) -> None:
        """Structured GitHub issue templates are present."""
        for relative_path in [
            ".github/ISSUE_TEMPLATE/bug_report.yml",
            ".github/ISSUE_TEMPLATE/feature_request.yml",
            ".github/ISSUE_TEMPLATE/docs_request.yml",
            ".github/ISSUE_TEMPLATE/endpoint_request.yml",
            ".github/ISSUE_TEMPLATE/config.yml",
        ]:
            self.assertTrue((PROJECT_ROOT / relative_path).exists(), relative_path)

    def test_issue_templates_collect_required_context_and_secret_warning(self) -> None:
        """Issue forms collect environment details and warn against secrets."""
        template_dir = PROJECT_ROOT / ".github" / "ISSUE_TEMPLATE"
        template_text = "\n".join(
            path.read_text(encoding="utf-8") for path in sorted(template_dir.glob("*.yml"))
        )

        for expected in [
            "PyProcore version",
            "Python version",
            "Operating system",
            "Command",
            "Expected behavior",
            "Actual behavior",
            "Sanitized logs",
            "live Procore API",
            "Procore endpoint",
            "tokens",
            "token stores",
            "Authorization headers",
            "private project data",
        ]:
            self.assertIn(expected, template_text)

    def test_pull_request_template_has_required_checklist(self) -> None:
        """Pull request template includes quality and no-secrets checklist items."""
        text = (PROJECT_ROOT / ".github" / "pull_request_template.md").read_text(encoding="utf-8")

        for expected in [
            "Tests added or updated",
            "Docs updated",
            "Examples updated if relevant",
            "make test",
            "make coverage",
            "make lint",
            "make typecheck",
            "black --check",
            "isort --check-only",
            "No secrets committed",
            "Changelog/release notes updated if relevant",
        ]:
            self.assertIn(expected, text)

    def test_dependabot_config_exists_for_pip_and_actions(self) -> None:
        """Dependabot checks Python dependencies and GitHub Actions weekly."""
        text = (PROJECT_ROOT / ".github" / "dependabot.yml").read_text(encoding="utf-8")

        self.assertIn("package-ecosystem: pip", text)
        self.assertIn("package-ecosystem: github-actions", text)
        self.assertIn("interval: weekly", text)
        self.assertIn("open-pull-requests-limit", text)

    def test_github_labels_guide_exists(self) -> None:
        """Suggested repository labels are documented."""
        text = (PROJECT_ROOT / "docs" / "github-labels.md").read_text(encoding="utf-8")

        for expected in [
            "bug",
            "enhancement",
            "documentation",
            "good first issue",
            "help wanted",
            "endpoint request",
            "automation",
            "auth",
            "workflows",
            "breaking change",
            "security",
            "needs reproduction",
        ]:
            self.assertIn(expected, text)

    def test_readme_links_to_community_docs(self) -> None:
        """README links contributor, security, support, and conduct docs."""
        readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")

        for expected in [
            "CONTRIBUTING.md",
            "SECURITY.md",
            "SUPPORT.md",
            "CODE_OF_CONDUCT.md",
            "docs/github-labels.md",
            "Contributing and Support",
        ]:
            self.assertIn(expected, readme)


if __name__ == "__main__":
    unittest.main()
