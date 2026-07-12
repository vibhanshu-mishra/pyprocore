"""Final release polish and readiness documentation tests."""

from __future__ import annotations

import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


class FinalReleasePolishTestCase(unittest.TestCase):
    """Validate final release-facing docs stay accurate."""

    def read_text(self, relative_path: str) -> str:
        """Read a repository file."""
        return (PROJECT_ROOT / relative_path).read_text(encoding="utf-8")

    def test_final_release_readiness_doc_exists(self) -> None:
        """Final readiness report should exist and cover release blockers."""
        report_path = PROJECT_ROOT / "docs/final-release-readiness.md"

        self.assertTrue(report_path.exists())
        report = self.read_text("docs/final-release-readiness.md")

        for phrase in (
            "Current Status",
            "Major Capabilities",
            "Validation Commands",
            "Known Limitations",
            "Live Procore Verification Limitations",
            "GitHub Workflow Token Limitation",
            "PyPI publishing has been completed for `2.1.0`",
            "Git tag `v2.1.0`",
            "Recommended Next Steps",
        ):
            self.assertIn(phrase, report)

    def test_readme_mentions_newer_release_features(self) -> None:
        """README should mention newer workflow, AI, automation, and security features."""
        readme = self.read_text("README.md")

        for phrase in (
            "project-context",
            "enhanced-rfi-package",
            "enhanced-submittal-package",
            "ai-review-export",
            "ai-prompt-pack",
            "workflow-plan",
            "webhook",
            "make secret-check",
            "Final release readiness",
        ):
            self.assertIn(phrase, readme)

    def test_changelog_summarizes_major_unreleased_phases(self) -> None:
        """Changelog should summarize the major release polish phases."""
        changelog = self.read_text("CHANGELOG.md")

        for phrase in (
            "Phase 3 expanded API coverage",
            "Phase 4 AI-ready project intelligence workflows",
            "Phase 5 automation foundation",
            "Phase 6 release readiness",
            "Phase 6E final release polish",
            "### Security",
            "### Tests",
        ):
            self.assertIn(phrase, changelog)

    def test_release_docs_pages_exist(self) -> None:
        """Key release-facing docs pages should exist."""
        for relative_path in (
            "docs/index.md",
            "docs/getting-started.md",
            "docs/authentication.md",
            "docs/cli.md",
            "docs/api-coverage.md",
            "docs/workflows.md",
            "docs/ai-review.md",
            "docs/agent-api.md",
            "docs/automation.md",
            "docs/security.md",
            "docs/release.md",
            "docs/recipes/index.md",
            "docs/final-release-readiness.md",
        ):
            self.assertTrue((PROJECT_ROOT / relative_path).exists(), relative_path)

    def test_examples_readme_mentions_latest_example_range(self) -> None:
        """Examples README should document the current 01 through 57 examples."""
        examples = self.read_text("examples/README.md")

        self.assertIn("01_list_companies.py", examples)
        self.assertIn("52_dispatch_webhook_to_workflow_plan.py", examples)
        self.assertIn("54_agent_manifest_export.py", examples)
        self.assertIn("55_agent_api_server.py", examples)
        self.assertIn("57_inspect_agent_schemas.py", examples)
        self.assertIn("runs from `01_list_companies.py` through", examples)

    def test_docs_claim_2_1_0_release_is_complete(self) -> None:
        """Release docs should describe the completed 2.1.0 release."""
        checked_docs = "\n".join(
            self.read_text(path)
            for path in (
                "docs/final-release-readiness.md",
                "docs/release.md",
                "README.md",
            )
        )

        self.assertIn("PyProcore `2.1.0` has been published to PyPI", checked_docs)
        self.assertIn("GitHub release was created", checked_docs)
        self.assertNotIn("PyPI publishing has not been performed for `2.1.0`", checked_docs)
        self.assertIn("not published as a hosted site", checked_docs)

    def test_live_verification_claims_are_limited(self) -> None:
        """Docs should describe live verification as manual and environment-specific."""
        report = self.read_text("docs/final-release-readiness.md")
        api_coverage = self.read_text("docs/api-coverage.md")

        self.assertIn("Smoke scripts", report)
        self.assertIn("project-level verification remains", report)
        self.assertIn("Procore access varies by environment", api_coverage)
        self.assertNotIn("all endpoints are live verified", report.lower())


if __name__ == "__main__":
    unittest.main()
