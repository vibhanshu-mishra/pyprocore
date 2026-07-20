"""Phase 9D private deployment and production runbook tests."""

from __future__ import annotations

import subprocess
import tempfile
import unittest
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from pyprocore import (
    __version__,
    build_enterprise_readiness_checklist,
    build_production_runbook_summary,
    evaluate_private_deployment_config,
    explain_private_deployment_pattern,
    sample_private_folder_layout,
)
from pyprocore.app import build_parser, format_enterprise_readiness_report, main, run_command
from pyprocore.workflows.deployment import EnterpriseReadinessFinding


class Phase9DPrivateDeploymentTests(unittest.TestCase):
    """Validate Phase 9D local-only private deployment behavior."""

    root = Path(__file__).resolve().parents[1]

    def test_enterprise_readiness_report_warns_for_risky_paths(self) -> None:
        """Readiness checks should warn for repo-local runtime paths."""
        report = evaluate_private_deployment_config(
            auth_mode="client_credentials",
            environment_name="production",
            token_store_path=self.root / "token_store.json",
            export_output_dir=self.root / "exports/private",
            log_dir=self.root / "logs/private",
            scheduled_export_plan_path=self.root / "examples/configs/plan.json",
            dry_run_required=False,
            repo_root=self.root,
        )
        codes = {finding.code for finding in report.findings}
        self.assertTrue(report.passed)
        self.assertIn("token_store_path_inside_repo", codes)
        self.assertIn("export_output_dir_inside_repo", codes)
        self.assertIn("log_dir_inside_repo", codes)
        self.assertIn("dry_run_not_required", codes)

    def test_enterprise_readiness_report_fails_for_bad_auth_mode(self) -> None:
        """Unsupported auth modes should be local validation failures."""
        report = evaluate_private_deployment_config(
            auth_mode="password",
            environment_name="production",
            token_store_path="/opt/pyprocore/token.json",
            export_output_dir="/opt/pyprocore/exports",
            log_dir="/opt/pyprocore/logs",
            repo_root=self.root,
        )
        self.assertFalse(report.passed)
        self.assertIn("unsupported_auth_mode", [finding.code for finding in report.findings])

    def test_server_to_server_recommends_client_credentials(self) -> None:
        """Server-to-server deployments should recommend client credentials."""
        report = evaluate_private_deployment_config(
            auth_mode="authorization_code",
            environment_name="production",
            token_store_path="/opt/pyprocore/token.json",
            export_output_dir="/opt/pyprocore/exports",
            log_dir="/opt/pyprocore/logs",
            repo_root=self.root,
        )
        self.assertIn("server_to_server_auth_mode", [finding.code for finding in report.findings])

    def test_pattern_layout_and_runbook_text_are_safe(self) -> None:
        """Deployment guidance helpers should be plain text and local-only."""
        self.assertIn("Client Credentials", "\n".join(build_enterprise_readiness_checklist()))
        self.assertIn("cron", explain_private_deployment_pattern("cron").casefold())
        self.assertIn("Docker", explain_private_deployment_pattern("docker"))
        self.assertIn("Unknown deployment pattern", explain_private_deployment_pattern("other"))
        self.assertIn("/opt/pyprocore", sample_private_folder_layout("/opt/pyprocore"))
        runbook = build_production_runbook_summary("client_credentials")
        self.assertTrue(any("Data Connection App" in item for item in runbook))
        self.assertNotIn("access_token", "\n".join(runbook))

    def test_cli_enterprise_commands_are_safe(self) -> None:
        """Enterprise CLI commands should not require credentials or live calls."""
        parser = build_parser()
        readiness_args = parser.parse_args(
            [
                "enterprise",
                "readiness-check",
                "--auth-mode",
                "client_credentials",
                "--environment-name",
                "production",
                "--token-store-path",
                "/opt/pyprocore/token-stores/production/token_store.json",
                "--output-dir",
                "/opt/pyprocore/exports/production",
                "--log-dir",
                "/opt/pyprocore/logs/production",
            ]
        )
        report = run_command(readiness_args)
        output = format_enterprise_readiness_report(report)
        self.assertIn("No Procore API calls were made", output)
        self.assertIn("MCP remains discovery-only", output)

        self.assertIn(
            "private server",
            run_command(
                parser.parse_args(
                    ["enterprise", "deployment-pattern", "--pattern", "private-server"]
                )
            ).casefold(),
        )
        self.assertIn(
            "token-stores",
            run_command(parser.parse_args(["enterprise", "sample-layout"])),
        )
        self.assertTrue(
            any(
                "Client Credentials" in item
                for item in run_command(parser.parse_args(["enterprise", "runbook-summary"]))
            )
        )

    def test_main_enterprise_json_and_text_outputs_are_safe(self) -> None:
        """Main should format enterprise commands safely."""
        parser = build_parser()
        with (
            patch("pyprocore.app.build_parser", return_value=parser),
            patch(
                "sys.argv",
                [
                    "procore-sdk",
                    "enterprise",
                    "readiness-check",
                    "--auth-mode",
                    "client_credentials",
                    "--environment-name",
                    "production",
                    "--json",
                ],
            ),
            patch("sys.stdout", new_callable=StringIO) as stdout,
        ):
            with self.assertRaises(SystemExit) as raised:
                main()
        self.assertEqual(raised.exception.code, 0)
        self.assertIn('"auth_mode": "client_credentials"', stdout.getvalue())
        self.assertNotIn("client_secret", stdout.getvalue())

        with (
            patch("pyprocore.app.build_parser", return_value=parser),
            patch("sys.argv", ["procore-sdk", "enterprise", "runbook-summary"]),
            patch("sys.stdout", new_callable=StringIO) as stdout,
        ):
            main()
        self.assertIn("Production Runbook Summary", stdout.getvalue())

    def test_scripts_are_local_only(self) -> None:
        """Phase 9D scripts should run without credentials."""
        commands = [
            [
                "python3",
                "scripts/enterprise_readiness_check.py",
                "--environment-name",
                "production",
            ],
            ["python3", "scripts/create_private_deployment_layout.py"],
            ["python3", "scripts/production_runbook_summary.py"],
        ]
        for command in commands:
            result = subprocess.run(
                command,
                cwd=self.root,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertNotIn("client_secret", result.stdout)

    def test_create_private_layout_requires_explicit_create(self) -> None:
        """Folder creation should be dry-run by default."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "runtime"
            dry_run = subprocess.run(
                ["python3", "scripts/create_private_deployment_layout.py", "--root", str(root)],
                cwd=self.root,
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertIn("Dry run only", dry_run.stdout)
            self.assertFalse(root.exists())

            created = subprocess.run(
                [
                    "python3",
                    "scripts/create_private_deployment_layout.py",
                    "--root",
                    str(root),
                    "--create",
                ],
                cwd=self.root,
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertIn("Created private deployment folders", created.stdout)
            self.assertTrue((root / "exports/production").is_dir())

    def test_templates_examples_and_docs_are_placeholder_only(self) -> None:
        """Deployment templates and examples should avoid real credentials."""
        deployment_dir = self.root / "examples/deployment"
        forbidden = (
            "sk_live",
            "ghp_",
            "xoxb-",
            "ya29.",
            "BEGIN PRIVATE KEY",
            "real-client-secret",
        )
        for path in deployment_dir.iterdir():
            content = path.read_text(encoding="utf-8")
            self.assertTrue(content.strip(), path.name)
            for marker in forbidden:
                self.assertNotIn(marker, content)
            self.assertNotIn("github-actions", path.name)

        examples_readme = (self.root / "examples/README.md").read_text(encoding="utf-8")
        self.assertIn("Examples `126` through `130`", examples_readme)

        docs = "\n".join(
            (self.root / name).read_text(encoding="utf-8")
            for name in (
                "docs/private-deployment.md",
                "docs/production-runbook.md",
                "docs/roadmap.md",
            )
        )
        self.assertIn("included in `v2.3.0`", docs)
        self.assertIn("Tool execution remains disabled", docs)
        self.assertIn("MCP remains discovery-only", docs)

    def test_safety_boundaries_remain_unchanged(self) -> None:
        """Phase 9D should not change release or execution boundaries."""
        self.assertEqual(__version__, "2.3.0")
        workflows = subprocess.run(
            ["git", "status", "--short", ".github/workflows"],
            cwd=self.root,
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertEqual(workflows.stdout.strip(), "")

        sources = "\n".join(
            path.read_text(encoding="utf-8")
            for path in [
                self.root / "pyprocore/workflows/deployment.py",
                self.root / "scripts/enterprise_readiness_check.py",
                self.root / "scripts/create_private_deployment_layout.py",
                self.root / "scripts/production_runbook_summary.py",
            ]
        )
        for marker in ("requests.", "boto3", "azure.keyvault", "google.cloud", "openai"):
            self.assertNotIn(marker, sources)
        self.assertNotIn("workflow_dispatch", sources)

    def test_readiness_finding_model(self) -> None:
        """Finding model should expose explicit severity values."""
        finding = EnterpriseReadinessFinding(
            severity="info",
            code="local_only",
            message="No live calls.",
        )
        self.assertEqual(finding.severity, "info")
