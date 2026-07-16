"""Phase 9B scheduled export planning tests."""

from __future__ import annotations

import json
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from pyprocore import (
    ScheduledExportManifest,
    ScheduledExportPlan,
    explain_scheduled_export_plan,
    load_scheduled_export_plan,
    sample_scheduled_export_plan_json,
    validate_scheduled_export_plan,
)
from pyprocore.app import (
    build_parser,
    format_scheduled_export_manifest,
    format_scheduled_export_validation,
    main,
    run_command,
)
from pyprocore.auth import permissions
from pyprocore.auth.permissions import (
    explain_app_connection_issue,
    explain_auth_error,
    explain_environment_mismatch,
    explain_permission_error,
)
from pyprocore.core.exceptions import ValidationError
from pyprocore.workflows.scheduled_exports import (
    SUPPORTED_RESOURCES,
    ScheduledExportFinding,
    _validate_output_dir,
    export_plan_to_manifest,
    write_scheduled_export_manifest,
)


class Phase9BScheduledExportTests(unittest.TestCase):
    """Validate local scheduled export planning behavior."""

    root = Path(__file__).resolve().parents[1]

    def test_plan_model_parses_sample_config(self) -> None:
        """Sample configs should parse to typed models."""
        plan = load_scheduled_export_plan(
            self.root / "examples/configs/scheduled_export_client_credentials.json"
        )
        self.assertIsInstance(plan, ScheduledExportPlan)
        self.assertEqual(plan.auth_mode, "client_credentials")
        self.assertEqual(plan.output_format, "csv")
        self.assertIn("rfis", plan.resources)

    def test_sample_configs_are_placeholder_only(self) -> None:
        """Sample configs should not include secrets or real-looking credentials."""
        config_dir = self.root / "examples/configs"
        for path in config_dir.glob("scheduled_export_*.json"):
            content = path.read_text(encoding="utf-8")
            payload = json.loads(content)
            self.assertNotIn("client_secret", content.casefold())
            self.assertNotIn("access_token", content.casefold())
            self.assertNotIn("refresh_token", content.casefold())
            self.assertIn(payload["company_id"], {12345})
            for project_id in payload.get("project_ids", []):
                self.assertIn(project_id, {67890, 11111, 22222})

    def test_validation_passes_for_valid_sample(self) -> None:
        """A valid sample should pass with no error findings."""
        report = validate_scheduled_export_plan(
            self.root / "examples/configs/scheduled_export_client_credentials.json"
        )
        self.assertTrue(report.is_valid)
        self.assertFalse(report.errors)
        self.assertTrue(any(finding.severity == "info" for finding in report.findings))

    def test_validation_fails_for_unknown_auth_mode(self) -> None:
        """Unknown auth modes should be rejected without credentials."""
        plan = ScheduledExportPlan(
            plan_name="bad-auth",
            auth_mode="password",
            company_id=12345,
            project_ids=[67890],
            resources=["rfis"],
        )
        report = validate_scheduled_export_plan(plan)
        self.assertFalse(report.is_valid)
        self.assertIn("unknown_auth_mode", [finding.code for finding in report.findings])

    def test_validation_fails_for_unknown_resource(self) -> None:
        """Unknown resources should be reported clearly."""
        plan = ScheduledExportPlan(
            plan_name="bad-resource",
            auth_mode="client_credentials",
            company_id=12345,
            project_ids=[67890],
            resources=["rfis", "not_a_resource"],
        )
        report = validate_scheduled_export_plan(plan)
        self.assertFalse(report.is_valid)
        self.assertIn("unknown_resource", [finding.code for finding in report.findings])
        self.assertIn("rfis", SUPPORTED_RESOURCES)

    def test_load_plan_rejects_invalid_files(self) -> None:
        """Plan loading should report local file problems without secrets."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaisesRegex(ValidationError, "must use .json"):
                load_scheduled_export_plan(root / "plan.yaml")
            with self.assertRaisesRegex(ValidationError, "file not found"):
                load_scheduled_export_plan(root / "missing.json")

            invalid_json = root / "invalid.json"
            invalid_json.write_text("{", encoding="utf-8")
            with self.assertRaisesRegex(ValidationError, "JSON is invalid"):
                load_scheduled_export_plan(invalid_json)

            array_json = root / "array.json"
            array_json.write_text("[]", encoding="utf-8")
            with self.assertRaisesRegex(ValidationError, "must be a JSON object"):
                load_scheduled_export_plan(array_json)

            extra_json = root / "extra.json"
            extra_json.write_text(
                json.dumps(
                    {
                        "plan_name": "extra",
                        "company_id": 12345,
                        "resources": ["companies"],
                        "client_secret": "fake-placeholder-secret",
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValidationError, "Scheduled export plan is invalid"):
                load_scheduled_export_plan(extra_json)

    def test_load_plan_wraps_local_read_errors(self) -> None:
        """Plan loading should wrap local read errors in SDK validation errors."""
        with tempfile.TemporaryDirectory() as directory:
            plan_directory = Path(directory) / "directory.json"
            plan_directory.mkdir()
            with self.assertRaisesRegex(ValidationError, "Could not read"):
                load_scheduled_export_plan(plan_directory)

    def test_validation_reports_common_configuration_errors(self) -> None:
        """Validation should catch missing scope and invalid options."""
        plan = ScheduledExportPlan(
            plan_name="bad-config",
            auth_mode="authorization_code",
            company_id=None,
            project_ids=[],
            resources=["rfis"],
            output_format="xlsx",
            output_dir=Path("../private-export"),
            max_projects=0,
            dry_run=False,
            redaction_enabled=False,
        )
        report = validate_scheduled_export_plan(plan)
        codes = {finding.code for finding in report.findings}
        self.assertFalse(report.is_valid)
        self.assertIn("authorization_code_scheduled_export", codes)
        self.assertIn("unknown_output_format", codes)
        self.assertIn("missing_company_id", codes)
        self.assertIn("missing_project_ids", codes)
        self.assertIn("parent_directory_output", codes)
        self.assertIn("invalid_max_projects", codes)
        self.assertIn("dry_run_disabled", codes)
        self.assertIn("redaction_disabled", codes)

    def test_validation_reports_missing_resources_and_output_dir(self) -> None:
        """Validation should report missing resources and missing output folders."""
        plan = ScheduledExportPlan(
            plan_name="missing-fields",
            auth_mode="client_credentials",
            company_id=12345,
            resources=[],
            output_dir=Path(" "),
        )
        report = validate_scheduled_export_plan(plan)
        codes = {finding.code for finding in report.findings}
        self.assertFalse(report.is_valid)
        self.assertIn("missing_resources", codes)
        self.assertIn("missing_output_dir", codes)

    def test_validation_rejects_remote_output_dir(self) -> None:
        """Remote URLs should not be accepted as scheduled export output folders."""

        class RemoteOutputPath:
            """Small path-like test double that preserves URL syntax."""

            parts: tuple[str, ...] = ()

            def __str__(self) -> str:
                return "s3://private-bucket/exports"

        plan = ScheduledExportPlan(
            plan_name="remote-output",
            auth_mode="client_credentials",
            company_id=12345,
            project_ids=[67890],
            resources=["rfis"],
        )
        plan.output_dir = RemoteOutputPath()  # type: ignore[assignment]
        findings: list[ScheduledExportFinding] = []
        _validate_output_dir(plan, findings)
        self.assertIn("remote_output_dir", [finding.code for finding in findings])

    def test_validation_reports_project_limit_exceeded(self) -> None:
        """Project limits should be enforced locally."""
        plan = ScheduledExportPlan(
            plan_name="too-many-projects",
            auth_mode="client_credentials",
            company_id=12345,
            project_ids=[67890, 11111],
            resources=["rfis"],
            max_projects=1,
        )
        report = validate_scheduled_export_plan(plan)
        self.assertFalse(report.is_valid)
        self.assertIn("project_limit_exceeded", [finding.code for finding in report.findings])

    def test_validation_warns_on_broad_multi_project_export(self) -> None:
        """Broad multi-project exports should warn when no limit is configured."""
        plan = ScheduledExportPlan(
            plan_name="broad-export",
            auth_mode="client_credentials",
            company_id=12345,
            project_ids=list(range(10000, 10012)),
            resources=["rfis"],
            max_projects=None,
        )
        report = validate_scheduled_export_plan(plan)
        self.assertTrue(report.is_valid)
        self.assertIn("broad_project_export", [finding.code for finding in report.warnings])

    def test_dry_run_manifest_generation(self) -> None:
        """Dry-run manifests should describe files without writing export data."""
        manifest = export_plan_to_manifest(
            self.root / "examples/configs/scheduled_export_client_credentials.json"
        )
        self.assertIsInstance(manifest, ScheduledExportManifest)
        self.assertTrue(manifest.dry_run)
        self.assertEqual(len(manifest.files), 4)
        self.assertTrue(all(str(file.output_path).endswith(".csv") for file in manifest.files))
        self.assertTrue(any("do not call Procore" in note for note in manifest.safety_notes))

    def test_dry_run_manifest_can_disable_timestamps_and_use_company_resources(self) -> None:
        """Dry-run manifests should support company resources and stable filenames."""
        plan = ScheduledExportPlan(
            plan_name="company-jsonl",
            auth_mode="authorization_code",
            company_id=12345,
            project_ids=[],
            resources=["companies", "vendors"],
            output_format="jsonl",
            output_dir=Path("./exports/company"),
            include_timestamp=False,
        )
        manifest = export_plan_to_manifest(plan)
        self.assertEqual(len(manifest.files), 2)
        self.assertTrue(all(file.project_id is None for file in manifest.files))
        self.assertTrue(all("{timestamp}" not in str(file.output_path) for file in manifest.files))
        self.assertTrue(all(str(file.output_path).endswith(".jsonl") for file in manifest.files))
        self.assertTrue(any("user-owned token store" in note for note in manifest.safety_notes))

    def test_human_explanation_path(self) -> None:
        """Human dry-run explanations should include safety notes and findings."""
        explanation = explain_scheduled_export_plan(
            self.root / "examples/configs/scheduled_export_authorization_code.json"
        )
        self.assertIn("Scheduled export dry run", explanation)
        self.assertIn("Authorization Code", explanation)
        self.assertIn("Safety notes", explanation)

    def test_write_manifest_is_explicit(self) -> None:
        """Dry-run manifests should write only when explicitly requested."""
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "manifest.json"
            result = write_scheduled_export_manifest(
                self.root / "examples/configs/scheduled_export_client_credentials.json",
                output,
            )
            self.assertEqual(result, output)
            manifest = json.loads(output.read_text(encoding="utf-8"))
            self.assertTrue(manifest["dry_run"])

    def test_cli_scheduled_export_commands(self) -> None:
        """CLI scheduled-export commands should route to local helpers."""
        parser = build_parser()
        sample_args = parser.parse_args(["scheduled-export", "sample-config"])
        sample = run_command(sample_args)
        self.assertIsInstance(sample, str)
        self.assertIn("client_credentials", sample)

        with tempfile.TemporaryDirectory() as directory:
            sample_output = Path(directory) / "sample.json"
            write_sample_args = parser.parse_args(
                ["scheduled-export", "sample-config", "--output", str(sample_output)]
            )
            self.assertEqual(run_command(write_sample_args), sample_output)
            self.assertTrue(sample_output.exists())

        validate_args = parser.parse_args(
            [
                "scheduled-export",
                "validate",
                "examples/configs/scheduled_export_client_credentials.json",
            ]
        )
        report = run_command(validate_args)
        self.assertTrue(report.is_valid)

        dry_run_args = parser.parse_args(
            [
                "scheduled-export",
                "dry-run",
                "examples/configs/scheduled_export_client_credentials.json",
                "--json",
            ]
        )
        manifest = run_command(dry_run_args)
        self.assertIsInstance(manifest, ScheduledExportManifest)

        with tempfile.TemporaryDirectory() as directory:
            manifest_output = Path(directory) / "dry-run.json"
            write_manifest_args = parser.parse_args(
                [
                    "scheduled-export",
                    "dry-run",
                    "examples/configs/scheduled_export_client_credentials.json",
                    "--write-manifest",
                    str(manifest_output),
                ]
            )
            self.assertEqual(run_command(write_manifest_args), manifest_output)
            self.assertTrue(manifest_output.exists())

    def test_cli_scheduled_export_json_validation_and_output_formatters(self) -> None:
        """CLI formatters should provide human and JSON-friendly scheduled output."""
        parser = build_parser()
        validate_json_args = parser.parse_args(
            [
                "scheduled-export",
                "validate",
                "examples/configs/scheduled_export_client_credentials.json",
                "--json",
            ]
        )
        report = run_command(validate_json_args)
        formatted_report = format_scheduled_export_validation(report)
        self.assertIn("Scheduled export plan validation complete", formatted_report)
        self.assertIn("Warnings:", formatted_report)

        dry_run_args = parser.parse_args(
            [
                "scheduled-export",
                "dry-run",
                "examples/configs/scheduled_export_client_credentials.json",
                "--json",
            ]
        )
        manifest = run_command(dry_run_args)
        formatted_manifest = format_scheduled_export_manifest(manifest)
        self.assertIn("Scheduled export dry run complete", formatted_manifest)
        self.assertIn("no Procore API calls", formatted_manifest)

    def test_cli_main_scheduled_export_output_paths(self) -> None:
        """CLI main should print scheduled-export results without live Procore calls."""
        with tempfile.TemporaryDirectory() as directory:
            sample_output = Path(directory) / "sample.json"
            manifest_output = Path(directory) / "manifest.json"
            output_commands = [
                [
                    "procore-sdk",
                    "scheduled-export",
                    "sample-config",
                    "--output",
                    str(sample_output),
                ],
                [
                    "procore-sdk",
                    "scheduled-export",
                    "dry-run",
                    "examples/configs/scheduled_export_client_credentials.json",
                    "--write-manifest",
                    str(manifest_output),
                ],
            ]
            for command in output_commands:
                with self.subTest(command=command):
                    output = StringIO()
                    with patch("sys.argv", command), redirect_stdout(output):
                        main()
                    self.assertIn("written", output.getvalue().casefold())

        commands = [
            [
                "procore-sdk",
                "scheduled-export",
                "sample-config",
                "--auth-mode",
                "authorization_code",
            ],
            [
                "procore-sdk",
                "scheduled-export",
                "validate",
                "examples/configs/scheduled_export_client_credentials.json",
            ],
            [
                "procore-sdk",
                "scheduled-export",
                "dry-run",
                "examples/configs/scheduled_export_client_credentials.json",
            ],
            [
                "procore-sdk",
                "scheduled-export",
                "dry-run",
                "examples/configs/scheduled_export_client_credentials.json",
                "--json",
            ],
        ]
        for command in commands:
            with self.subTest(command=command):
                output = StringIO()
                with patch("sys.argv", command), redirect_stdout(output):
                    try:
                        main()
                    except SystemExit as exc:
                        self.assertEqual(exc.code, 0)
                self.assertIn("scheduled", output.getvalue().casefold())

    def test_auth_permission_explanations_are_safe_and_mode_aware(self) -> None:
        """Auth guidance helpers should explain common statuses without secrets."""
        unauthorized = explain_auth_error(
            401,
            {"error": "expired", "access_token": "secret-token"},
            "client_credentials",
        )
        self.assertIn("client-credentials", unauthorized)
        self.assertIn("expired", unauthorized)
        self.assertNotIn("secret-token", unauthorized)

        delegated = explain_auth_error(401, "expired refresh needed", "authorization_code")
        self.assertIn("Reauthorize", delegated)

        forbidden = explain_permission_error(403, auth_mode="client_credentials")
        self.assertIn("Data Connection App", forbidden)

        generic = explain_auth_error(418, {"detail": "short safe message"})
        self.assertIn("HTTP 418", generic)
        self.assertIn("short safe message", generic)

        app_connection = explain_app_connection_issue("authorization_code")
        self.assertIn("authenticated user's", app_connection)

        mismatch = explain_environment_mismatch(
            "https://login-sandbox.procore.com",
            "https://api.procore.com",
        )
        self.assertIn("different environments", mismatch)

        aligned = explain_environment_mismatch(
            "https://login.procore.com",
            "https://api.procore.com",
        )
        self.assertIn("same Procore environment", aligned)

        self.assertIsNone(
            permissions._safe_error_summary("token leaked")  # type: ignore[attr-defined]
        )
        self.assertIn(
            "safe",
            permissions._safe_error_summary({"safe": "value"}) or "",  # type: ignore[attr-defined]
        )

    def test_lazy_module_exports_and_unknown_attributes(self) -> None:
        """Lazy package exports should resolve known helpers and reject unknown names."""
        import pyprocore.auth as auth_module
        import pyprocore.core as core_module

        self.assertIs(auth_module.__getattr__("explain_auth_error"), explain_auth_error)
        self.assertIs(core_module.__getattr__("ValidationError"), ValidationError)
        with self.assertRaises(AttributeError):
            auth_module.__getattr__("missing_helper")
        with self.assertRaises(AttributeError):
            core_module.__getattr__("missing_helper")

    def test_validation_and_dry_run_do_not_call_procore(self) -> None:
        """Validation and dry-run planning should not call live SDK clients."""
        with patch("pyprocore.core.client.ProcoreClient.get") as get_mock:
            validate_scheduled_export_plan(
                self.root / "examples/configs/scheduled_export_client_credentials.json"
            )
            export_plan_to_manifest(
                self.root / "examples/configs/scheduled_export_client_credentials.json"
            )
        get_mock.assert_not_called()

    def test_docs_and_examples_state_safety_boundaries(self) -> None:
        """Docs should keep Phase 9B unreleased and local-only."""
        readme = (self.root / "README.md").read_text(encoding="utf-8")
        docs_page = (self.root / "docs/enterprise-scheduled-exports.md").read_text(encoding="utf-8")
        examples_readme = (self.root / "examples/README.md").read_text(encoding="utf-8")
        self.assertIn("Phase 9B", readme)
        self.assertIn("unreleased", docs_page.casefold())
        self.assertIn("do not call Procore", docs_page)
        self.assertIn("Examples `115` through `120`", examples_readme)

    def test_no_workflow_files_reference_phase9b_commands(self) -> None:
        """Phase 9B should not add or change GitHub Actions workflows."""
        workflows_dir = self.root / ".github/workflows"
        for path in workflows_dir.glob("*"):
            if path.is_file():
                content = path.read_text(encoding="utf-8")
                self.assertNotIn("scheduled-export", content)

    def test_tool_execution_and_mcp_remain_disabled_in_docs(self) -> None:
        """Safety docs should preserve disabled execution language."""
        docs_page = (self.root / "docs/enterprise-scheduled-exports.md").read_text(encoding="utf-8")
        self.assertIn("Tool execution remains disabled", docs_page)
        self.assertIn("MCP", docs_page)
        self.assertIn("discovery-only", docs_page)

    def test_sample_json_helper_uses_placeholders(self) -> None:
        """Generated samples should contain placeholders and no secret fields."""
        sample = sample_scheduled_export_plan_json()
        self.assertIn("12345", sample)
        self.assertNotIn("client_secret", sample.casefold())
        self.assertNotIn("access_token", sample.casefold())


if __name__ == "__main__":
    unittest.main()
