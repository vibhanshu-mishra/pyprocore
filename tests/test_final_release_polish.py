"""Public release polish and status documentation tests."""

from __future__ import annotations

import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


class FinalReleasePolishTestCase(unittest.TestCase):
    """Validate public release-facing docs stay accurate."""

    def read_text(self, relative_path: str) -> str:
        """Read a repository file."""
        return (PROJECT_ROOT / relative_path).read_text(encoding="utf-8")

    def test_internal_final_readiness_doc_is_not_public(self) -> None:
        """Internal readiness report should not be tracked as public docs."""
        report_path = PROJECT_ROOT / "docs/final-release-readiness.md"

        self.assertFalse(report_path.exists())

    def test_project_status_doc_exists(self) -> None:
        """Project status page should provide the public release summary."""
        report = self.read_text("docs/project-status.md")
        for phrase in (
            "Current Versions",
            "Current Stable Release: 2.2.0",
            "Previous Stable Release: 2.1.0",
            "Safety Status",
            "Known Limitations",
            "Current stable release: `2.2.0`",
            "Previous stable release: `2.1.0`",
            "Tool execution remains disabled",
            "MCP adapter remains discovery-only",
            "Future Roadmap",
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
            "Project Status",
            "Phase 7 Agent Layer",
        ):
            self.assertIn(phrase, readme)

    def test_changelog_summarizes_major_release_phases(self) -> None:
        """Changelog should summarize the major released phases."""
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
            "docs/project-status.md",
        ):
            self.assertTrue((PROJECT_ROOT / relative_path).exists(), relative_path)

    def test_examples_readme_mentions_latest_example_range(self) -> None:
        """Examples README should document the current 01 through 79 examples."""
        examples = self.read_text("examples/README.md")

        self.assertIn("01_list_companies.py", examples)
        self.assertIn("52_dispatch_webhook_to_workflow_plan.py", examples)
        self.assertIn("54_agent_manifest_export.py", examples)
        self.assertIn("55_agent_api_server.py", examples)
        self.assertIn("57_inspect_agent_schemas.py", examples)
        self.assertIn("59_replay_agent_run.py", examples)
        self.assertIn("61_mcp_discovery_only.py", examples)
        self.assertIn("63_inspect_agent_eval_results.py", examples)
        self.assertIn("64_list_observations.py", examples)
        self.assertIn("69_agent_registry_phase8a.py", examples)
        self.assertIn("70_configure_client_credentials.py", examples)
        self.assertIn("73_auth_modes_overview.py", examples)
        self.assertIn("74_list_meetings.py", examples)
        self.assertIn("79_agent_registry_phase8c.py", examples)
        self.assertIn("runs from `01_list_companies.py` through", examples)

    def test_docs_claim_2_2_0_release_is_complete(self) -> None:
        """Release docs should describe the completed 2.2.0 release."""
        checked_docs = "\n".join(
            self.read_text(path)
            for path in (
                "docs/project-status.md",
                "docs/release.md",
                "README.md",
            )
        )

        self.assertIn("PyProcore `2.2.0` has been published to PyPI", checked_docs)
        self.assertIn("released on GitHub", checked_docs)
        self.assertNotIn("2.2.0 has not been published", checked_docs)

    def test_live_verification_claims_are_limited(self) -> None:
        """Docs should describe live verification as manual and environment-specific."""
        report = self.read_text("docs/project-status.md")
        api_coverage = self.read_text("docs/api-coverage.md")

        self.assertIn("Live project-level behavior can vary", report)
        self.assertIn("Procore access varies by environment", api_coverage)
        self.assertNotIn("all endpoints are live verified", report.lower())


if __name__ == "__main__":
    unittest.main()
