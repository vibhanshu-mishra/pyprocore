"""Tests for release-candidate validation tooling."""

from __future__ import annotations

import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


class ReleaseCandidateTestCase(unittest.TestCase):
    """Validate release-candidate checks stay local and non-publishing."""

    def read_text(self, relative_path: str) -> str:
        """Read a repository file.

        Args:
            relative_path: Path relative to the project root.
        """
        return (PROJECT_ROOT / relative_path).read_text(encoding="utf-8")

    def test_release_candidate_script_exists(self) -> None:
        """Release-candidate checker should exist as a local script."""
        self.assertTrue((PROJECT_ROOT / "scripts/check_release_candidate.py").exists())

    def test_makefile_has_release_candidate_targets(self) -> None:
        """Makefile should expose package build and RC validation targets."""
        makefile = self.read_text("Makefile")

        self.assertIn("release-candidate-check:", makefile)
        self.assertIn("scripts/check_release_candidate.py", makefile)
        self.assertIn("build-package:", makefile)
        self.assertIn("$(PYTHON) -m build", makefile)

    def test_release_docs_mention_release_candidate_validation(self) -> None:
        """Release docs should explain local artifact validation."""
        release_doc = self.read_text("docs/release.md")

        self.assertIn("Release Candidate Validation", release_doc)
        self.assertIn("make release-candidate-check", release_doc)
        self.assertIn("clean temporary virtual environment", release_doc)
        self.assertIn("does not publish anything", release_doc)

    def test_final_readiness_mentions_release_candidate_check(self) -> None:
        """Final readiness report should mention RC validation as completed tooling."""
        report = self.read_text("docs/final-release-readiness.md")

        self.assertIn("release-candidate validation step", report)
        self.assertIn("make release-candidate-check", report)
        self.assertIn("Release-candidate package check passed", report)

    def test_gitignore_excludes_release_artifacts(self) -> None:
        """Release build artifacts and temporary release envs should be ignored."""
        gitignore = self.read_text(".gitignore")

        for pattern in ("dist/", "build/", "*.egg-info/", ".venv-release/"):
            self.assertIn(pattern, gitignore)

    def test_script_supports_required_flags(self) -> None:
        """The script should support strict, artifact, build, and verbose options."""
        script = self.read_text("scripts/check_release_candidate.py")

        for flag in ("--strict", "--keep-artifacts", "--skip-build", "--verbose"):
            self.assertIn(flag, script)

    def test_script_does_not_publish_or_call_live_procore(self) -> None:
        """The RC checker should not upload packages or call Procore APIs."""
        script = self.read_text("scripts/check_release_candidate.py").lower()

        forbidden_phrases = (
            "twine upload",
            "upload.pypi.org",
            "test.pypi.org/legacy",
            "api.procore.com",
            "login.procore.com",
            "procore-sdk companies",
            "procore-sdk projects",
            "procore-sdk doctor --live",
        )
        for phrase in forbidden_phrases:
            self.assertNotIn(phrase, script)


if __name__ == "__main__":
    unittest.main()
