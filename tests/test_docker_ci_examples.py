"""Tests for Docker and CI automation examples."""

from __future__ import annotations

import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


class DockerCIExamplesTestCase(unittest.TestCase):
    """Validate Docker and CI templates without running external tools."""

    def test_dockerfile_exists_and_is_secret_safe(self) -> None:
        """The Dockerfile uses a slim Python image and does not include secrets."""
        dockerfile = PROJECT_ROOT / "Dockerfile"
        source = dockerfile.read_text(encoding="utf-8")

        self.assertIn("FROM python:3.12-slim", source)
        self.assertIn("WORKDIR /app", source)
        self.assertIn("pip install", source)
        self.assertIn('CMD ["procore-sdk", "--help"]', source)
        self.assertIn("USER pyprocore", source)
        self.assertNotIn("PROCORE_CLIENT_SECRET=", source)
        self.assertNotIn("token_store.json", source)

    def test_dockerignore_excludes_secrets_and_outputs(self) -> None:
        """The Docker build context excludes secrets, token stores, and outputs."""
        dockerignore = (PROJECT_ROOT / ".dockerignore").read_text(encoding="utf-8")

        for expected in [
            ".env",
            ".env.*",
            "token_store.json",
            "pyprocore/auth/token_store.json",
            "downloads",
            "logs",
            "webhook-events",
            "*.pyc",
        ]:
            self.assertIn(expected, dockerignore)

    def test_root_docker_compose_is_safe_default(self) -> None:
        """The root compose file runs a safe default command."""
        compose = (PROJECT_ROOT / "docker-compose.yml").read_text(encoding="utf-8")

        self.assertIn("pyprocore:", compose)
        self.assertIn("procore-sdk", compose)
        self.assertIn("--help", compose)
        self.assertIn("PROCORE_CLIENT_ID", compose)
        self.assertIn("workflow-plan", compose)
        self.assertNotIn("your_client_secret", compose)

    def test_docker_example_files_exist(self) -> None:
        """Docker helper scripts and compose examples are present."""
        for relative_path in [
            "examples/docker/README.md",
            "examples/docker/workflow-runner.docker-compose.yml",
            "examples/docker/run-workflow-in-docker.sh",
            "examples/docker/run-workflow-in-docker.ps1",
        ]:
            self.assertTrue((PROJECT_ROOT / relative_path).exists(), relative_path)

        shell_script = (PROJECT_ROOT / "examples/docker/run-workflow-in-docker.sh").read_text(
            encoding="utf-8"
        )
        powershell_script = (PROJECT_ROOT / "examples/docker/run-workflow-in-docker.ps1").read_text(
            encoding="utf-8"
        )
        self.assertIn("docker build", shell_script)
        self.assertIn("workflow-plan run", shell_script)
        self.assertIn("--dry-run", shell_script)
        self.assertIn("docker build", powershell_script)
        self.assertIn("workflow-plan run", powershell_script)

    def test_github_actions_docker_workflow_is_dry_run_template(self) -> None:
        """The Docker GitHub Actions example builds and dry-runs safely."""
        workflow = (
            PROJECT_ROOT / "examples/github-actions/pyprocore-docker-workflow.yml"
        ).read_text(encoding="utf-8")

        self.assertIn("docker build", workflow)
        self.assertIn("procore-sdk --help", workflow)
        self.assertIn("workflow-plan validate", workflow)
        self.assertIn("workflow-plan run", workflow)
        self.assertIn("--dry-run", workflow)
        self.assertIn("actions/upload-artifact", workflow)
        self.assertNotIn("PROCORE_CLIENT_SECRET:", workflow)

    def test_env_example_has_required_keys_and_warnings(self) -> None:
        """The environment example documents required keys without secrets."""
        env_example = (PROJECT_ROOT / ".env.example").read_text(encoding="utf-8")

        for expected in [
            "PROCORE_CLIENT_ID=",
            "PROCORE_CLIENT_SECRET=",
            "PROCORE_REDIRECT_URI=http://localhost",
            "PROCORE_LOGIN_URL=https://login.procore.com",
            "PROCORE_API_BASE=https://api.procore.com",
            "PROCORE_COMPANY_ID=",
        ]:
            self.assertIn(expected, env_example)
        self.assertIn("Do not commit real .env", env_example)
        self.assertIn("token-store strategy", env_example)

    def test_docs_and_readme_reference_docker_ci(self) -> None:
        """Docker and CI docs are linked from user-facing documentation."""
        for relative_path in [
            "docs/automation/docker.md",
            "docs/automation/ci.md",
        ]:
            self.assertTrue((PROJECT_ROOT / relative_path).exists(), relative_path)

        readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
        examples_readme = (PROJECT_ROOT / "examples/README.md").read_text(encoding="utf-8")
        self.assertIn("Docker Automation", readme)
        self.assertIn("CI Automation", readme)
        self.assertIn("examples/docker", readme)
        self.assertIn("Docker examples", examples_readme)

    def test_makefile_has_optional_docker_targets(self) -> None:
        """Optional Docker targets are available without changing core targets."""
        makefile = (PROJECT_ROOT / "Makefile").read_text(encoding="utf-8")

        self.assertIn("docker-build:", makefile)
        self.assertIn("docker-help:", makefile)
        self.assertIn("docker-run-plan:", makefile)
        self.assertIn("PLAN ?=", makefile)


if __name__ == "__main__":
    unittest.main()
