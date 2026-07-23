"""Tests for Phase 17C local integration blueprint support."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import pyprocore
from pyprocore.core.exceptions import ValidationError
from pyprocore.integrations import (
    IntegrationBlueprint,
    append_sync_log,
    build_integration_readiness_report,
    build_sample_webhook_event,
    complete_sync_run,
    compute_webhook_signature,
    create_sync_run,
    fail_sync_run,
    get_integration_blueprint,
    integration_blueprint_to_json,
    integration_blueprint_to_markdown,
    integration_blueprints_to_json,
    integration_blueprints_to_markdown,
    integration_readiness_report_to_json,
    integration_readiness_report_to_markdown,
    list_integration_blueprints,
    normalize_webhook_event,
    read_sync_run,
    summarize_sync_runs,
    sync_run_summary_to_json,
    sync_run_summary_to_markdown,
    verify_webhook_signature,
    write_webhook_event,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]


class Phase17CIntegrationBlueprintTests(unittest.TestCase):
    """Validate local-only integration blueprint metadata."""

    def run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        """Run the local CLI without requiring credentials."""
        env = {**os.environ, "PYTHONPATH": str(PROJECT_ROOT)}
        return subprocess.run(
            [sys.executable, "-m", "pyprocore.app", *args],
            cwd=PROJECT_ROOT,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_builtin_blueprints_load_with_safety_boundaries(self) -> None:
        """Built-in blueprints should exist and remain metadata-only."""
        blueprints = list_integration_blueprints()
        names = {blueprint.name for blueprint in blueprints}

        self.assertIn("procore_to_csv_sync_worker", names)
        self.assertIn("procore_webhook_receiver", names)
        self.assertIn("procore_fastapi_read_api", names)
        self.assertIn("procore_dashboard_data_bridge", names)
        self.assertEqual(len(blueprints), 7)
        self.assertTrue(hasattr(pyprocore, "list_integration_blueprints"))
        for blueprint in blueprints:
            self.assertIsInstance(blueprint, IntegrationBlueprint)
            self.assertTrue(blueprint.metadata_only)
            self.assertFalse(blueprint.execution_enabled)
            self.assertFalse(blueprint.procore_api_call_required)
            self.assertFalse(blueprint.write_enabled)
            self.assertFalse(blueprint.hosted_app_included)
            self.assertFalse(blueprint.database_dependency_required)
            self.assertFalse(blueprint.automatic_scheduler_enabled)
            self.assertFalse(blueprint.remote_call_enabled)
            self.assertFalse(blueprint.external_ai_required)
            self.assertFalse(blueprint.mcp_execution_enabled)

    def test_blueprint_reports_render_json_and_markdown(self) -> None:
        """Blueprint inventory and detail reports should serialize cleanly."""
        blueprints = list_integration_blueprints()
        blueprint = get_integration_blueprint("procore_project_health_feed")

        inventory_payload = json.loads(integration_blueprints_to_json(blueprints, pretty=True))
        detail_payload = json.loads(integration_blueprint_to_json(blueprint, pretty=True))
        inventory_markdown = integration_blueprints_to_markdown(blueprints)
        detail_markdown = integration_blueprint_to_markdown(blueprint)

        self.assertEqual(inventory_payload[0]["mode"], "local_integration_blueprint_metadata_only")
        self.assertEqual(detail_payload["name"], "procore_project_health_feed")
        self.assertIn("Integration Blueprints", inventory_markdown)
        self.assertIn("No Procore API calls", detail_markdown)
        with self.assertRaisesRegex(KeyError, "Unknown integration blueprint"):
            get_integration_blueprint("missing-blueprint")

    def test_readiness_checks_produce_findings(self) -> None:
        """Readiness checks should warn about local setup gaps without credentials."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "exports"
            report = build_integration_readiness_report(
                "procore_webhook_receiver",
                output_dir,
                env={"PROCORE_CLIENT_SECRET": "changeme"},
                token_store_path=PROJECT_ROOT / "token_store.json",
                sync_log_dir=Path(temp_dir) / "logs",
            )
            payload = json.loads(integration_readiness_report_to_json(report, pretty=True))
            markdown = integration_readiness_report_to_markdown(report)
            codes = {finding["code"] for finding in payload["findings"]}

            self.assertFalse(payload["procore_api_call_required"])
            self.assertIn("required_env_missing", codes)
            self.assertIn("placeholder_secret", codes)
            self.assertIn("webhook_secret_missing", codes)
            self.assertIn("Integration Readiness Report", markdown)

    def test_readiness_checks_cover_local_path_variants(self) -> None:
        """Readiness checks should handle existing, created, and invalid output paths."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            existing_output_dir = temp_path / "exports"
            existing_output_dir.mkdir()
            sync_log_dir = temp_path / "logs"
            sync_log_dir.mkdir()
            outside_token_path = Path(tempfile.gettempdir()) / "pyprocore-token-store.json"
            env = {
                "PROCORE_CLIENT_ID": "client-id",
                "PROCORE_CLIENT_SECRET": "realistic-secret",
                "PROCORE_REDIRECT_URI": "http://localhost/callback",
                "PROCORE_LOGIN_URL": "https://login.example.test",
                "PROCORE_API_BASE": "https://api.example.test",
                "PROCORE_COMPANY_ID": "123",
            }

            existing_report = build_integration_readiness_report(
                "procore_to_csv_sync_worker",
                existing_output_dir,
                env=env,
                token_store_path=outside_token_path,
                sync_log_dir=sync_log_dir,
            )
            created_report = build_integration_readiness_report(
                "procore_to_jsonl_sync_worker",
                temp_path / "created",
                env=env,
                create_output_dir=True,
            )
            file_output = temp_path / "not-a-directory"
            file_output.write_text("not a directory\n", encoding="utf-8")
            file_report = build_integration_readiness_report(
                "procore_dashboard_data_bridge",
                file_output,
                env=env,
            )

            existing_codes = {finding.code for finding in existing_report.findings}
            created_codes = {finding.code for finding in created_report.findings}
            file_codes = {finding.code for finding in file_report.findings}

            self.assertIn("output_dir_exists", existing_codes)
            self.assertIn("required_env_present", existing_codes)
            self.assertIn("token_store_outside_repo", existing_codes)
            self.assertIn("sync_log_dir_exists", existing_codes)
            self.assertIn("output_dir_created", created_codes)
            self.assertIn("output_path_not_directory", file_codes)
            self.assertTrue((temp_path / "created").is_dir())

    def test_sync_run_lifecycle_writes_local_records_and_redacts(self) -> None:
        """Sync run helpers should write local JSON/JSONL records only."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "sync"
            run = create_sync_run(
                "procore_to_csv_sync_worker",
                output_dir,
                run_id="unit_run",
                summary={"client_secret": "very-secret"},
            )
            entry = append_sync_log(
                run,
                "Bearer should-not-leak",
                data={"access_token": "token-value", "nested": {"password": "secret"}},
            )
            completed = complete_sync_run(run, summary={"records": 3})
            failed = fail_sync_run(completed, "refresh_token=secret-value", summary={"errors": 1})
            reloaded = read_sync_run(output_dir / "unit_run.json")
            summary = summarize_sync_runs(output_dir)
            summary_markdown = sync_run_summary_to_markdown(summary)
            summary_payload = json.loads(sync_run_summary_to_json(summary, pretty=True))
            log_text = (output_dir / "unit_run.jsonl").read_text(encoding="utf-8")

            self.assertEqual(entry.data["access_token"], "[REDACTED]")
            self.assertEqual(reloaded.status.value, "failed")
            self.assertEqual(reloaded.summary["client_secret"], "[REDACTED]")
            self.assertIn("[REDACTED]", reloaded.error_message or "")
            self.assertIn("[REDACTED]", log_text)
            self.assertNotIn("token-value", log_text)
            self.assertEqual(summary_payload["run_count"], 1)
            self.assertIn("Local Sync Run Summary", summary_markdown)
            self.assertEqual(failed.status.value, "failed")

    def test_sync_run_error_paths_and_empty_summary(self) -> None:
        """Sync run helpers should report invalid records and empty summaries cleanly."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            empty_dir = temp_path / "empty"
            empty_dir.mkdir()
            invalid_run_path = temp_path / "invalid.json"
            invalid_run_path.write_text("{not valid json", encoding="utf-8")
            empty_summary = summarize_sync_runs(empty_dir)
            empty_markdown = sync_run_summary_to_markdown(empty_summary)

            self.assertEqual(empty_summary["run_count"], 0)
            self.assertIn("| none | 0 |", empty_markdown)
            with self.assertRaisesRegex(ValidationError, "Could not read sync run record"):
                read_sync_run(invalid_run_path)

    def test_webhook_hmac_fixture_passes_and_fails(self) -> None:
        """Webhook helpers should verify local HMAC fixtures deterministically."""
        secret = "local-secret"
        body = {"event_type": "rfi.updated", "resource_id": 15}
        signature = compute_webhook_signature(body, secret)
        event = normalize_webhook_event(
            {"X-Test-Signature": signature},
            body,
            signature_header="X-Test-Signature",
            secret=secret,
            event_id="evt_unit",
        )

        self.assertTrue(verify_webhook_signature(body, signature, secret))
        self.assertFalse(verify_webhook_signature(body, signature, "wrong-secret"))
        self.assertTrue(event.signature_valid)

        with tempfile.TemporaryDirectory() as temp_dir:
            json_path = Path(temp_dir) / "event.json"
            jsonl_path = Path(temp_dir) / "events.jsonl"
            write_webhook_event(event, json_path)
            write_webhook_event(event, jsonl_path)
            sample = build_sample_webhook_event(Path(temp_dir) / "sample.json")
            self.assertTrue(json_path.exists())
            self.assertTrue(jsonl_path.read_text(encoding="utf-8").strip())
            self.assertTrue(sample.signature_valid)

    def test_webhook_body_variants_and_append_mode(self) -> None:
        """Webhook helpers should normalize bytes, strings, and non-object JSON safely."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "events.txt"
            dict_body = {"raw": "Bearer should-redact"}
            bytes_body = b'{"resource_id": 10}'
            list_body = "[1, 2, 3]"
            raw_body = "not-json"

            bytes_event = normalize_webhook_event({}, bytes_body, event_id="evt_bytes")
            list_event = normalize_webhook_event({}, list_body, event_id="evt_list")
            raw_event = normalize_webhook_event({}, raw_body, event_id="evt_raw")
            redacted_event = normalize_webhook_event(
                {"Authorization": "Bearer should-redact"},
                dict_body,
                event_id="evt_redacted",
            )
            write_webhook_event(bytes_event, output_path, append_jsonl=True)
            write_webhook_event(list_event, output_path, append_jsonl=True)

            self.assertEqual(bytes_event.body["resource_id"], 10)
            self.assertEqual(list_event.body["body"], [1, 2, 3])
            self.assertEqual(raw_event.body["raw_body"], "not-json")
            self.assertEqual(redacted_event.headers["Authorization"], "Bearer [REDACTED]")
            self.assertEqual(redacted_event.body["raw"], "Bearer [REDACTED]")
            self.assertEqual(len(output_path.read_text(encoding="utf-8").splitlines()), 2)

    def test_cli_integration_commands_work_without_credentials(self) -> None:
        """Integration CLI commands should run locally without Procore access."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "outputs"
            event_path = Path(temp_dir) / "event.json"
            commands = [
                ("integrations", "blueprints", "--json"),
                ("integrations", "blueprint", "procore_to_csv_sync_worker", "--format", "json"),
                (
                    "integrations",
                    "readiness",
                    "procore_to_csv_sync_worker",
                    "--output-dir",
                    str(output_dir),
                    "--format",
                    "json",
                ),
                (
                    "integrations",
                    "sync-run",
                    "sample",
                    "--output-dir",
                    str(output_dir),
                    "--json",
                ),
                (
                    "integrations",
                    "sync-run",
                    "summarize",
                    str(output_dir),
                    "--format",
                    "json",
                ),
                ("integrations", "webhook", "sample-event", "--output", str(event_path), "--json"),
                (
                    "integrations",
                    "webhook",
                    "verify",
                    "--event",
                    str(event_path),
                    "--secret",
                    "local-test-secret",
                    "--secret-is-value",
                    "--json",
                ),
            ]
            results = [self.run_cli(*command) for command in commands]

            for completed in results:
                self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn("procore_to_csv_sync_worker", results[0].stdout)
            self.assertEqual(json.loads(results[1].stdout)["name"], "procore_to_csv_sync_worker")
            self.assertFalse(json.loads(results[2].stdout)["procore_api_call_required"])
            self.assertEqual(json.loads(results[4].stdout)["run_count"], 1)
            self.assertTrue(json.loads(results[6].stdout)["verified"])
            self.assertFalse(json.loads(results[6].stdout)["secret_echoed"])

    def test_cli_integration_markdown_and_env_secret_paths(self) -> None:
        """Integration CLI commands should also cover human-readable output paths."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            output_dir = temp_path / "outputs"
            event_path = temp_path / "event.json"

            sample_result = self.run_cli(
                "integrations",
                "webhook",
                "sample-event",
                "--output",
                str(event_path),
            )
            env = {
                **os.environ,
                "PYTHONPATH": str(PROJECT_ROOT),
                "LOCAL_WEBHOOK_SECRET": "local-test-secret",
            }
            verify_result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pyprocore.app",
                    "integrations",
                    "webhook",
                    "verify",
                    "--event",
                    str(event_path),
                    "--secret",
                    "LOCAL_WEBHOOK_SECRET",
                ],
                cwd=PROJECT_ROOT,
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )
            commands = [
                ("integrations", "blueprints"),
                ("integrations", "blueprint", "procore_to_csv_sync_worker", "--format", "markdown"),
                (
                    "integrations",
                    "readiness",
                    "procore_to_csv_sync_worker",
                    "--output-dir",
                    str(output_dir),
                    "--format",
                    "markdown",
                ),
                (
                    "integrations",
                    "sync-run",
                    "sample",
                    "--output-dir",
                    str(output_dir),
                ),
                (
                    "integrations",
                    "sync-run",
                    "summarize",
                    str(output_dir),
                    "--format",
                    "markdown",
                ),
            ]
            results = [self.run_cli(*command) for command in commands]

            self.assertEqual(sample_result.returncode, 0, sample_result.stderr)
            self.assertEqual(verify_result.returncode, 0, verify_result.stderr)
            for completed in results:
                self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn("# Integration Blueprints", results[0].stdout)
            self.assertIn("# Procore to CSV Sync Worker", results[1].stdout)
            self.assertIn("# Integration Readiness Report", results[2].stdout)
            self.assertIn("# Local Sync Run Summary", results[4].stdout)
            self.assertIn('"verified": true', verify_result.stdout)
            self.assertNotIn("local-test-secret", verify_result.stdout)

    def test_source_does_not_enable_network_execution_or_writes(self) -> None:
        """Integration package source should not include forbidden execution behavior."""
        integration_files = sorted((PROJECT_ROOT / "pyprocore" / "integrations").glob("*.py"))
        forbidden_snippets = [
            "import requests",
            "from requests",
            "import httpx",
            "from httpx",
            "import urllib.request",
            "from urllib",
            "import subprocess",
            "from subprocess",
            "import importlib",
            "from importlib",
            "api.procore.com",
            "procore.com/rest",
            "exec(",
            "eval(",
            ".post(",
            ".put(",
            ".delete(",
            "import redis",
            "import psycopg",
            "import sqlalchemy",
            "from sqlalchemy",
        ]
        for path in integration_files:
            source = path.read_text(encoding="utf-8").casefold()
            for snippet in forbidden_snippets:
                self.assertNotIn(snippet.casefold(), source, f"{snippet} found in {path}")


if __name__ == "__main__":
    unittest.main()
