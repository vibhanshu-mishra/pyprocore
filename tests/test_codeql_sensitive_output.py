"""Regression tests for CodeQL clear-text sensitive-output findings."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import Mock, patch

from pyprocore.app import format_configuration_error, main, to_serializable
from pyprocore.auth.oauth import OAuthClient
from pyprocore.core.config import ProcoreSettings, get_settings
from pyprocore.core.exceptions import AuthenticationError, ConfigurationError, ProcoreAPIError
from pyprocore.core.logger import log_exception, structured_message
from pyprocore.core.redaction import REDACTED, redact_sensitive_text, safe_for_logging
from pyprocore.dmsa import (
    GcOwnerInstallationPacketOptions,
    build_dmsa_connection_profile,
    build_gc_owner_installation_packet,
    dmsa_connection_summary_to_markdown,
    dmsa_report_to_json,
    gc_owner_installation_packet_to_markdown,
    gc_owner_packet_to_json,
    redact_dmsa_connection_profile,
    summarize_dmsa_connection_profile,
)
from pyprocore.intake import (
    IntakeSyncConfig,
    IntakeSyncFinding,
    intake_to_json,
    intake_validation_to_markdown,
    run_intake_sync_with_records,
    write_intake_sync_outputs,
)
from pyprocore.plugins import (
    PluginTrustFinding,
    PluginTrustPolicy,
    PluginTrustReport,
    render_trust_report_markdown,
    trust_report_to_json,
)
from pyprocore.workflows.automation_runner import _write_json, _write_markdown

RAW_VALUES = {
    "client_secret": "client_secret_should_not_appear",
    "access_token": "access_token_should_not_appear",
    "refresh_token": "refresh_token_should_not_appear",
    "authorization": "Bearer bearer_token_should_not_appear",
    "api_key": "sk_test_should_not_appear",
}


class CodeqlSensitiveOutputTests(unittest.TestCase):
    """Prove sensitive fixtures cannot cross public output boundaries."""

    def assert_redacted(self, rendered: str) -> None:
        """Assert every raw sentinel is absent and a redaction marker remains."""
        for raw_value in RAW_VALUES.values():
            self.assertNotIn(raw_value, rendered)
        self.assertIn(REDACTED, rendered)

    def test_central_redaction_handles_nested_keys_text_and_urls(self) -> None:
        """Central redaction covers fields, assignments, bearer text, and queries."""
        payload = {
            **RAW_VALUES,
            "nested": [
                "client_secret=client_secret_should_not_appear",
                "https://example.test/file?token=access_token_should_not_appear&safe=yes",
                "https://example.test/file?X-Goog-Signature=refresh_token_should_not_appear",
            ],
            "token_store_path": "/safe/token_store.json",
            "client_secret_env_var": "PROCORE_CLIENT_SECRET",
            "secret": False,
            "secret_echoed": False,
        }

        rendered = json.dumps(safe_for_logging(payload), sort_keys=True)

        self.assert_redacted(rendered)
        self.assertIn("/safe/token_store.json", rendered)
        self.assertIn("PROCORE_CLIENT_SECRET", rendered)
        self.assertIn("safe=yes", rendered)
        self.assertIn('"secret": false', rendered)
        self.assertIn('"secret_echoed": false', rendered)

    def test_text_redaction_keeps_json_documents_valid(self) -> None:
        """Text sinks can sanitize serialized JSON without corrupting its syntax."""
        source = json.dumps({"secret": False, "client_secret": RAW_VALUES["client_secret"]})

        rendered = redact_sensitive_text(source)

        self.assertIs(json.loads(rendered)["secret"], False)
        self.assertNotIn(RAW_VALUES["client_secret"], rendered)

    def test_logger_and_oauth_error_body_use_central_redaction(self) -> None:
        """Logs and OAuth failures must not retain response credentials."""
        log_output = structured_message("codeql_regression", payload=RAW_VALUES)
        oauth_output = json.dumps(OAuthClient._redact_error_body(RAW_VALUES))

        self.assert_redacted(log_output)
        self.assert_redacted(oauth_output)

    def test_exception_log_omits_sensitive_chained_cause(self) -> None:
        """Traceback logging keeps context while omitting raw chained inputs."""
        logger = Mock()
        try:
            try:
                raise ValueError("client_secret_should_not_appear")
            except ValueError as cause:
                raise ConfigurationError("Configuration validation failed.") from cause
        except ConfigurationError as error:
            log_exception(logger, exc=error)

        entry = json.loads(logger.error.call_args.args[0])
        self.assertEqual(entry["exception_type"], "ConfigurationError")
        self.assertNotIn("client_secret_should_not_appear", entry["stack_trace"])
        self.assertIn("Configuration validation failed.", entry["stack_trace"])

    def test_api_exception_redacts_message_and_attached_response_body(self) -> None:
        """Exception attributes and text stay safe for future consumers."""
        error = ProcoreAPIError(
            "Authorization: Bearer bearer_token_should_not_appear",
            status_code=403,
            response_body=RAW_VALUES,
        )

        self.assertNotIn("bearer_token_should_not_appear", str(error))
        self.assert_redacted(json.dumps(error.response_body))

    def test_oauth_invalid_response_does_not_echo_sensitive_response_values(self) -> None:
        """OAuth schema errors omit rejected credential values from diagnostics."""
        session = Mock()
        response = Mock()
        response.ok = True
        response.json.return_value = {
            "access_token": RAW_VALUES["access_token"],
            "refresh_token": RAW_VALUES["refresh_token"],
            "client_secret": RAW_VALUES["client_secret"],
        }
        session.post.return_value = response
        client = OAuthClient(
            settings=ProcoreSettings(
                client_id="sample-id",
                client_secret="sample-secret",
                redirect_uri="http://localhost/callback",
                login_url="https://login.example.test",
                api_base="https://api.example.test",
                company_id=123,
            ),
            session=session,
        )

        with self.assertRaises(AuthenticationError) as context:
            client.request_client_credentials_token()

        message = str(context.exception)
        for raw_value in RAW_VALUES.values():
            self.assertNotIn(raw_value, message)
        self.assertIn("expires_in", message)

    def test_invalid_environment_error_does_not_echo_rejected_input(self) -> None:
        """Configuration errors identify the field without echoing its value."""
        raw_value = "client_secret_should_not_appear"
        with (
            patch.dict(
                "os.environ",
                {
                    "PROCORE_CLIENT_ID": "sample-id",
                    "PROCORE_CLIENT_SECRET": "sample-secret",
                    "PROCORE_REDIRECT_URI": "http://localhost/callback",
                    "PROCORE_LOGIN_URL": "https://login.example.test",
                    "PROCORE_API_BASE": "https://api.example.test",
                    "PROCORE_COMPANY_ID": raw_value,
                },
                clear=True,
            ),
            patch("pyprocore.core.config._load_dotenv"),
        ):
            get_settings.cache_clear()
            try:
                with self.assertRaises(ConfigurationError) as context:
                    get_settings()
            finally:
                get_settings.cache_clear()

        self.assertNotIn(raw_value, str(context.exception))
        self.assertIn("company_id", str(context.exception))

    def test_cli_serialization_and_main_output_redact_sensitive_values(self) -> None:
        """The CLI boundary sanitizes arbitrary command result mappings."""
        serialized = json.dumps(to_serializable(RAW_VALUES))
        self.assert_redacted(serialized)

        stdout = StringIO()
        with (
            patch.object(sys, "argv", ["procore-sdk", "companies"]),
            patch("pyprocore.app.run_command", return_value=RAW_VALUES),
            redirect_stdout(stdout),
        ):
            main()

        self.assert_redacted(stdout.getvalue())

    def test_cli_exception_details_redact_embedded_assignments(self) -> None:
        """Configuration diagnostics preserve context without exposing values."""
        rendered = format_configuration_error(
            ConfigurationError(
                "client_secret=client_secret_should_not_appear "
                "Authorization: Bearer bearer_token_should_not_appear"
            )
        )

        self.assertNotIn("client_secret_should_not_appear", rendered)
        self.assertNotIn("bearer_token_should_not_appear", rendered)
        self.assertIn(REDACTED, rendered)

    def test_dmsa_profile_json_never_serializes_secret_values(self) -> None:
        """DMSA JSON keeps env-var references but redacts hostile note text."""
        profile = build_dmsa_connection_profile(
            company_id=123,
            notes=["client_secret=client_secret_should_not_appear"],
        )

        redacted_profile = json.dumps(redact_dmsa_connection_profile(profile))
        report_json = dmsa_report_to_json(profile)

        self.assert_redacted(redacted_profile)
        self.assert_redacted(report_json)
        self.assertIn("PROCORE_CLIENT_SECRET", report_json)

    def test_dmsa_profile_env_reference_must_be_a_variable_name(self) -> None:
        """DMSA env-var fields cannot be used as a channel for secret values."""
        profile = build_dmsa_connection_profile(
            company_id=123,
            client_secret_env_var="client_secret_should_not_appear",
        )

        output = redact_dmsa_connection_profile(profile)

        self.assertEqual(output["client_secret_env_var"], REDACTED)
        self.assertNotIn("client_secret_should_not_appear", json.dumps(output))

    def test_dmsa_profile_redacts_app_version_key_reference(self) -> None:
        """App Version Key references are not exposed in serialized profiles."""
        profile = build_dmsa_connection_profile(
            company_id=123,
            app_version_key_reference="client_secret_should_not_appear",
        )

        output = json.dumps(redact_dmsa_connection_profile(profile))

        self.assertNotIn("client_secret_should_not_appear", output)
        self.assertIn(REDACTED, output)

    def test_dmsa_summary_redacts_invalid_credential_references(self) -> None:
        """DMSA human-readable summaries preserve only env-var names."""
        profile = build_dmsa_connection_profile(
            company_id=123,
            client_id_env_var="client_secret_should_not_appear",
            client_secret_env_var="access_token_should_not_appear",
        )
        summary = summarize_dmsa_connection_profile(profile)
        rendered = dmsa_connection_summary_to_markdown(summary)

        self.assertEqual(summary.credential_references["client_id_env_var"], REDACTED)
        self.assertEqual(summary.credential_references["client_secret_env_var"], REDACTED)
        self.assert_redacted(rendered)

    def test_plugin_trust_json_and_markdown_redact_sensitive_metadata(self) -> None:
        """Local plugin reports sanitize target identity, policy, and findings."""
        report = PluginTrustReport(
            target_type="manifest",
            target_name="client_secret=client_secret_should_not_appear",
            trusted=False,
            valid=False,
            finding_count=1,
            findings=[
                PluginTrustFinding(
                    severity="error",
                    code="unsafe_metadata",
                    message="access_token=access_token_should_not_appear",
                )
            ],
            policy=PluginTrustPolicy(
                allowed_publishers=["PyProcore"],
                notes=["sk_test_should_not_appear"],
            ),
        )

        self.assert_redacted(trust_report_to_json(report))
        self.assert_redacted(render_trust_report_markdown(report))

    def test_intake_saved_outputs_redact_credentials_and_signed_urls(self) -> None:
        """All local intake exports sanitize raw, normalized, and URL fields."""
        record = {
            "id": 501,
            "number": "RFI-15",
            "title": "client_secret=client_secret_should_not_appear",
            "access_token": RAW_VALUES["access_token"],
            "attachments": [
                {
                    "id": 9001,
                    "filename": "drawing.pdf",
                    "url": (
                        "https://files.example.test/drawing.pdf?"
                        "token=refresh_token_should_not_appear&download=1"
                    ),
                }
            ],
        }
        config = IntakeSyncConfig(
            profile_name="local-test",
            project_ids=[123],
            include_submittals=False,
            output_dir="./unused",
        )
        result = run_intake_sync_with_records(config, {123: [record]}, {})

        with tempfile.TemporaryDirectory() as temporary_directory:
            output_root = Path(temporary_directory) / "exports"
            write_intake_sync_outputs(result, output_root, dry_run=False)
            rendered_files = "\n".join(
                path.read_text(encoding="utf-8")
                for path in output_root.rglob("*")
                if path.is_file()
            )

        self.assertNotIn("client_secret_should_not_appear", rendered_files)
        self.assertNotIn("access_token_should_not_appear", rendered_files)
        self.assertNotIn("refresh_token_should_not_appear", rendered_files)
        self.assertIn(REDACTED, rendered_files)

    def test_workflow_json_and_markdown_writers_redact_sensitive_values(self) -> None:
        """Workflow files are sanitized at their final local-write boundary."""
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            json_path = _write_json(root / "manifest.json", RAW_VALUES)
            markdown_path = _write_markdown(
                root / "summary.md",
                "client_secret=client_secret_should_not_appear",
            )
            json_text = json_path.read_text(encoding="utf-8")
            markdown_text = markdown_path.read_text(encoding="utf-8")

        self.assert_redacted(json_text)
        self.assertNotIn("client_secret_should_not_appear", markdown_text)
        self.assertIn(REDACTED, markdown_text)

    def test_plugin_trust_example_uses_safe_report_renderer(self) -> None:
        """The standalone trust example sends report text through the sanitizer."""
        example_path = (
            Path(__file__).resolve().parents[1]
            / "examples"
            / "282_validate_plugin_trust_manifest.py"
        )
        source = example_path.read_text(encoding="utf-8")

        self.assertIn("render_trust_report_markdown(report)", source)
        self.assertNotIn("sk_test_should_not_appear", source)

    def test_gc_owner_json_and_markdown_redact_dynamic_values(self) -> None:
        """Packet renderers sanitize user-provided names and support text."""
        packet = build_gc_owner_installation_packet(
            GcOwnerInstallationPacketOptions(
                consultant_name="client_secret=client_secret_should_not_appear",
                gc_owner_name="access_token=access_token_should_not_appear",
                support_contact="Authorization: Bearer bearer_token_should_not_appear",
            )
        )

        self.assert_redacted(gc_owner_packet_to_json(packet))
        self.assert_redacted(gc_owner_installation_packet_to_markdown(packet))

    def test_intake_json_and_markdown_redact_finding_text(self) -> None:
        """Intake report formats redact secret-like source findings."""
        finding = IntakeSyncFinding(
            level="warning",
            code="source_error",
            message="refresh_token=refresh_token_should_not_appear",
        )

        self.assert_redacted(intake_to_json({"finding": finding.model_dump()}))
        self.assert_redacted(intake_validation_to_markdown([finding]))

    def test_embedded_text_redaction_is_case_insensitive(self) -> None:
        """Mixed-case credential labels cannot bypass text redaction."""
        rendered = redact_sensitive_text(
            "Client_Secret=client_secret_should_not_appear; "
            "AUTHORIZATION: Bearer bearer_token_should_not_appear"
        )

        self.assertNotIn("client_secret_should_not_appear", rendered)
        self.assertNotIn("bearer_token_should_not_appear", rendered)
        self.assertIn(REDACTED, rendered)


if __name__ == "__main__":
    unittest.main()
