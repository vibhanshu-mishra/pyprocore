"""Tests for Phase 19A local DMSA connection profiles."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pyprocore
from pyprocore.app import build_parser, main, run_command
from pyprocore.client import Procore
from pyprocore.core.config import AuthMode, get_settings
from pyprocore.core.exceptions import ConfigurationError, ValidationError
from pyprocore.dmsa import (
    build_dmsa_connection_profile,
    build_dmsa_installation_packet,
    build_dmsa_permission_checklist,
    build_dmsa_smoke_check_plan,
    diagnose_dmsa_permission_issue,
    dmsa_connection_summary_to_markdown,
    dmsa_installation_packet_to_markdown,
    dmsa_permission_checklist_to_markdown,
    dmsa_permission_diagnostic_to_markdown,
    dmsa_report_to_json,
    dmsa_smoke_check_plan_to_markdown,
    dmsa_validation_report_to_markdown,
    load_dmsa_connection_profile,
    redact_dmsa_connection_profile,
    settings_from_dmsa_connection_profile,
    summarize_dmsa_connection_profile,
    validate_dmsa_connection_profile,
    write_dmsa_connection_profile_template,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
FIXTURE = PROJECT_ROOT / "examples" / "dmsa" / "dmsa_connection_profile.json"


class Phase19ADmsaProfileTests(unittest.TestCase):
    """Validate safe, local-only DMSA profile behavior."""

    def run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        """Run the local CLI without credentials."""
        env = {
            key: value
            for key, value in os.environ.items()
            if key not in {"PROCORE_CLIENT_ID", "PROCORE_CLIENT_SECRET"}
        }
        env["PYTHONPATH"] = str(PROJECT_ROOT)
        return subprocess.run(
            [sys.executable, "-m", "pyprocore.app", *args],
            cwd=PROJECT_ROOT,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_profile_build_load_and_root_exports(self) -> None:
        """Profiles should be typed, local, and exported from the package root."""
        profile = load_dmsa_connection_profile(FIXTURE)

        self.assertEqual(profile.company_id, 123456)
        self.assertEqual(profile.client_secret_env_var, "PROCORE_CLIENT_SECRET")
        self.assertTrue(hasattr(pyprocore, "DmsaConnectionProfile"))
        self.assertTrue(hasattr(pyprocore, "build_dmsa_permission_checklist"))

    def test_profile_builder_rejects_conflicting_inputs(self) -> None:
        """Builder should reject ambiguous model-plus-keyword input."""
        profile_input = pyprocore.DmsaConnectionProfileInput(company_id=1)
        with self.assertRaises(ValidationError):
            build_dmsa_connection_profile(profile_input, profile_name="duplicate")

    def test_sample_template_is_secret_free_and_protected(self) -> None:
        """Generated JSON should name env vars and refuse accidental overwrite."""
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "profile.json"
            written = write_dmsa_connection_profile_template(path)
            payload = json.loads(written.read_text(encoding="utf-8"))

            self.assertEqual(payload["client_id_env_var"], "PROCORE_CLIENT_ID")
            self.assertEqual(payload["client_secret_env_var"], "PROCORE_CLIENT_SECRET")
            serialized = json.dumps(payload)
            self.assertNotIn("actual-client-secret", serialized)
            with self.assertRaises(ValidationError):
                write_dmsa_connection_profile_template(path)
            self.assertEqual(
                write_dmsa_connection_profile_template(path, overwrite=True),
                path.resolve(),
            )

    def test_template_rejects_traversal_and_non_json(self) -> None:
        """Template output should reject ambiguous or traversing paths."""
        with self.assertRaises(ValidationError):
            write_dmsa_connection_profile_template("../profile.json")
        with self.assertRaises(ValidationError):
            write_dmsa_connection_profile_template("profile.yaml")

    def test_load_rejects_invalid_local_documents(self) -> None:
        """Profile loading should explain invalid JSON and object shape."""
        with tempfile.TemporaryDirectory() as temp_dir:
            invalid = Path(temp_dir) / "invalid.json"
            invalid.write_text("{", encoding="utf-8")
            with self.assertRaises(ValidationError):
                load_dmsa_connection_profile(invalid)
            invalid.write_text("[]", encoding="utf-8")
            with self.assertRaises(ValidationError):
                load_dmsa_connection_profile(invalid)
            with self.assertRaises(ValidationError):
                load_dmsa_connection_profile(Path(temp_dir) / "profile.yaml")
            invalid.write_text('{"company_id": "not-an-id"}', encoding="utf-8")
            with self.assertRaises(ValidationError):
                load_dmsa_connection_profile(invalid)
            with self.assertRaises(ValidationError):
                load_dmsa_connection_profile(Path(temp_dir) / "missing.json")

    def test_validation_finds_required_metadata_and_project_warning(self) -> None:
        """Structural validation should catch missing IDs and credential references."""
        profile = build_dmsa_connection_profile(
            profile_name="incomplete",
            company_id=None,
            allowed_project_ids=[],
            client_id_env_var=None,
            client_secret_env_var=None,
        )
        report = validate_dmsa_connection_profile(profile)
        codes = {finding.code for finding in report.findings}

        self.assertFalse(report.valid)
        self.assertIn("missing_company_id", codes)
        self.assertIn("missing_client_id_env_var", codes)
        self.assertIn("missing_client_secret_env_var", codes)
        self.assertIn("no_allowed_projects", codes)

        invalid_values = build_dmsa_connection_profile(
            company_id=1,
            allowed_project_ids=[-1],
            client_id_env_var="not valid",
            client_secret_env_var="also-invalid",
        )
        invalid_report = validate_dmsa_connection_profile(invalid_values)
        invalid_codes = {finding.code for finding in invalid_report.findings}
        self.assertIn("invalid_project_id", invalid_codes)
        self.assertIn("invalid_client_id_env_var", invalid_codes)
        self.assertIn("invalid_client_secret_env_var", invalid_codes)

    def test_redaction_hides_secret_looking_notes(self) -> None:
        """Reports should retain env-var names while redacting secret-like values."""
        profile = build_dmsa_connection_profile(
            profile_name="redaction",
            company_id=1,
            allowed_project_ids=[2],
            notes=["client_secret=do-not-print", "access_token:abc123"],
        )
        redacted = redact_dmsa_connection_profile(profile)
        summary = summarize_dmsa_connection_profile(profile)

        self.assertIn("[REDACTED]", " ".join(redacted["notes"]))
        self.assertEqual(redacted["client_secret_env_var"], "PROCORE_CLIENT_SECRET")
        self.assertNotIn("do-not-print", dmsa_report_to_json(summary))
        with_secret_extra = build_dmsa_connection_profile(
            company_id=1,
            allowed_project_ids=[2],
            actual_secret="hidden",
        )
        self.assertEqual(
            redact_dmsa_connection_profile(with_secret_extra)["actual_secret"],
            "[REDACTED]",
        )

    def test_client_factory_reuses_client_credentials_without_token_request(self) -> None:
        """Factory creation should resolve existing auth settings but remain lazy."""
        profile = load_dmsa_connection_profile(FIXTURE)
        with (
            patch.dict(
                os.environ,
                {
                    "PROCORE_CLIENT_ID": "fake-client-id",
                    "PROCORE_CLIENT_SECRET": "fake-client-secret",
                },
                clear=False,
            ),
            patch(
                "pyprocore.auth.oauth.OAuthClient.request_client_credentials_token"
            ) as token_request,
        ):
            settings = settings_from_dmsa_connection_profile(profile)
            client = Procore.from_dmsa_profile(profile)
            file_client = Procore.from_dmsa_profile_file(FIXTURE)
            observed_company_ids: list[int] = []

            def capture_projects(*, company_id: int) -> list[object]:
                observed_company_ids.append(get_settings().company_id)
                self.assertEqual(company_id, 123456)
                return []

            with patch("pyprocore.client.list_projects", side_effect=capture_projects):
                self.assertEqual(client.projects.list(), [])

        self.assertEqual(settings.auth_mode, AuthMode.CLIENT_CREDENTIALS)
        self.assertEqual(settings.company_id, 123456)
        self.assertEqual(observed_company_ids, [123456])
        self.assertIsInstance(client, Procore)
        self.assertIsInstance(file_client, Procore)
        token_request.assert_not_called()

    def test_client_factory_reports_missing_named_credentials(self) -> None:
        """Factory should fail safely when referenced env vars are absent."""
        profile = load_dmsa_connection_profile(FIXTURE)
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(ConfigurationError, "PROCORE_CLIENT_ID"):
                Procore.from_dmsa_profile(profile)

    def test_permission_checklist_and_packet_are_explicit(self) -> None:
        """GC/Owner guidance should describe least privilege and ownership."""
        checklist = build_dmsa_permission_checklist()
        packet = build_dmsa_installation_packet()
        checklist_text = dmsa_permission_checklist_to_markdown(checklist)
        packet_text = dmsa_installation_packet_to_markdown(packet)

        self.assertIn("RFIs: Read Only", checklist_text)
        self.assertIn("Submittals: Read Only", checklist_text)
        self.assertIn("GC/Owner controls", checklist.summary)
        self.assertIn("does not create a DMSA", packet_text)
        self.assertIn("No write actions are enabled", packet_text)

    def test_smoke_plan_is_complete_and_non_executing(self) -> None:
        """Smoke planning should cover intended reads without enabling execution."""
        plan = build_dmsa_smoke_check_plan(load_dmsa_connection_profile(FIXTURE))
        text = dmsa_smoke_check_plan_to_markdown(plan)
        titles = " ".join(item.title for item in plan.items)

        self.assertFalse(plan.live_execution_enabled)
        for concept in ("token", "projects", "RFIs", "Submittals", "attachment"):
            self.assertIn(concept.casefold(), titles.casefold())
        self.assertIn("does not call Procore", text)

    def test_permission_diagnostics_cover_common_local_summaries(self) -> None:
        """Diagnostics should provide likely causes for expected status contexts."""
        cases: list[tuple[dict[str, Any], str]] = [
            ({"status_code": 401}, "client credentials"),
            ({"status_code": 403}, "lacks permission"),
            ({"status_code": 404, "context": "project"}, "project/resource ID"),
            ({"context": "projects", "empty_result": True}, "permitted projects"),
            ({"context": "rfis", "empty_result": True}, "RFIs"),
            ({"context": "submittals", "empty_result": True}, "Submittals"),
            ({"context": "rfis", "missing_attachments": True}, "Attachment permissions"),
        ]
        for arguments, expected in cases:
            with self.subTest(arguments=arguments):
                report = diagnose_dmsa_permission_issue(**arguments)
                rendered = dmsa_permission_diagnostic_to_markdown(report)
                self.assertIn(expected, rendered)
                self.assertIn("Likely cause", rendered)
                self.assertIn("Recommended review", rendered)
        insufficient = diagnose_dmsa_permission_issue()
        self.assertEqual(insufficient.findings[0].code, "insufficient_context")

    def test_json_and_markdown_reports_render(self) -> None:
        """All report families should support JSON or Markdown output."""
        profile = load_dmsa_connection_profile(FIXTURE)
        validation = validate_dmsa_connection_profile(profile)
        self.assertEqual(json.loads(dmsa_report_to_json(validation))["valid"], True)
        self.assertIn("DMSA Profile Validation", dmsa_validation_report_to_markdown(validation))
        self.assertIn(
            "DMSA Connection",
            dmsa_connection_summary_to_markdown(summarize_dmsa_connection_profile(profile)),
        )
        self.assertEqual(json.loads(dmsa_report_to_json({"safe": True})), {"safe": True})

        no_findings = validation.model_copy(update={"findings": []})
        self.assertIn(
            "No structural findings",
            dmsa_validation_report_to_markdown(no_findings),
        )

    def test_cli_commands_work_without_credentials(self) -> None:
        """Every DMSA metadata command should run locally without Procore access."""
        commands = [
            ("validate-profile", str(FIXTURE), "--format", "json"),
            ("summarize-profile", str(FIXTURE), "--format", "markdown"),
            ("permission-checklist", "--format", "json"),
            ("installation-packet", "--format", "markdown"),
            ("smoke-plan", str(FIXTURE), "--format", "json"),
            ("diagnose", "--status-code", "403", "--context", "rfis"),
        ]
        for command in commands:
            with self.subTest(command=command):
                result = self.run_cli("dmsa", *command)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertTrue(result.stdout.strip())
                self.assertNotIn("Traceback", result.stderr)

    def test_cli_commands_are_covered_in_process(self) -> None:
        """Parser, command dispatch, and renderers should be tested without subprocess gaps."""
        parser = build_parser()
        commands = [
            ["dmsa", "validate-profile", str(FIXTURE), "--format", "json"],
            ["dmsa", "summarize-profile", str(FIXTURE)],
            ["dmsa", "permission-checklist"],
            ["dmsa", "installation-packet"],
            ["dmsa", "smoke-plan", str(FIXTURE)],
            ["dmsa", "diagnose", "--status-code", "403", "--context", "rfis"],
        ]
        for command in commands:
            with self.subTest(command=command):
                arguments = parser.parse_args(command)
                result = run_command(arguments)
                self.assertIsNotNone(result)
                output = StringIO()
                with patch.object(sys, "argv", ["procore-sdk", *command]), redirect_stdout(output):
                    main()
                self.assertTrue(output.getvalue().strip())

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "profile.json"
            command = [
                "dmsa",
                "sample-profile",
                "--output",
                str(output_path),
            ]
            output = StringIO()
            with patch.object(sys, "argv", ["procore-sdk", *command]), redirect_stdout(output):
                main()
            self.assertTrue(output_path.exists())
            self.assertIn("written to", output.getvalue())

    def test_cli_validation_failure_exits_one(self) -> None:
        """Invalid local profile metadata should produce a nonzero CLI status."""
        with tempfile.TemporaryDirectory() as temp_dir:
            profile_path = Path(temp_dir) / "invalid.json"
            profile_path.write_text(
                json.dumps(
                    build_dmsa_connection_profile(
                        company_id=None,
                        client_id_env_var=None,
                        client_secret_env_var=None,
                    ).model_dump(mode="json")
                ),
                encoding="utf-8",
            )
            with (
                patch.object(
                    sys,
                    "argv",
                    [
                        "procore-sdk",
                        "dmsa",
                        "validate-profile",
                        str(profile_path),
                    ],
                ),
                redirect_stdout(StringIO()),
                self.assertRaises(SystemExit) as raised,
            ):
                main()
            self.assertEqual(raised.exception.code, 1)

    def test_cli_sample_profile_and_examples_are_local(self) -> None:
        """CLI template output and examples should not require credentials."""
        with tempfile.TemporaryDirectory() as temp_dir:
            result = self.run_cli(
                "dmsa",
                "sample-profile",
                "--output",
                str(Path(temp_dir) / "sample.json"),
            )
            self.assertEqual(result.returncode, 0, result.stderr)
        for number in range(335, 341):
            example = next(PROJECT_ROOT.glob(f"examples/{number}_*.py"))
            result = subprocess.run(
                [sys.executable, str(example)],
                cwd=PROJECT_ROOT,
                env={"PYTHONPATH": str(PROJECT_ROOT)},
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, f"{example}: {result.stderr}")

    def test_phase19a_contains_no_network_or_write_execution(self) -> None:
        """DMSA modules should remain metadata-only and add no mutation verbs."""
        source = "\n".join(
            path.read_text(encoding="utf-8")
            for path in (PROJECT_ROOT / "pyprocore" / "dmsa").glob("*.py")
        ).casefold()
        self.assertNotIn("requests.", source)
        self.assertNotIn("httpx.", source)
        self.assertNotIn("mcp execution enabled", source)
        for signature in (".post(", ".put(", ".patch(", ".delete("):
            self.assertNotIn(signature, source)


if __name__ == "__main__":
    unittest.main()
