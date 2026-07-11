"""Unit tests for local webhook helper utilities."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from pyprocore import app
from pyprocore.core.exceptions import ValidationError
from pyprocore.webhooks import (
    WebhookEvent,
    WebhookEventStoreResult,
    dispatch_webhook_event,
    list_webhook_events,
    normalize_webhook_event,
    parse_webhook_event,
    redact_webhook_payload,
    save_webhook_event,
)
from pyprocore.workflows.models import (
    WorkflowPlan,
    WorkflowRunManifest,
    WorkflowRunResult,
    WorkflowStep,
)


class WebhookHelpersTestCase(unittest.TestCase):
    """Validate webhook parsing, normalization, storage, and dispatch helpers."""

    def test_parse_valid_event_from_json_string(self) -> None:
        """JSON strings normalize into typed webhook events."""
        event = parse_webhook_event(
            json.dumps(
                {
                    "event_id": "evt-1",
                    "event_type": "rfi.created",
                    "action": "created",
                    "company_id": 456,
                    "project_id": 123,
                    "resource": {"type": "rfi", "id": 99},
                }
            )
        )

        self.assertEqual(event.event_id, "evt-1")
        self.assertEqual(event.event_type, "rfi.created")
        self.assertEqual(event.resource_type, "rfi")
        self.assertEqual(event.resource_id, "99")
        self.assertEqual(event.project_id, "123")

    def test_parse_rejects_invalid_json(self) -> None:
        """Invalid JSON raises a friendly SDK validation error."""
        with self.assertRaises(ValidationError):
            parse_webhook_event("{not-json")

    def test_normalize_nested_data_resource_payload(self) -> None:
        """Nested data/resource webhook shapes are handled defensively."""
        event = normalize_webhook_event(
            {
                "id": "evt-2",
                "type": "submittal.updated",
                "data": {
                    "action": "updated",
                    "companyId": 456,
                    "projectId": 123,
                    "resource": {
                        "resource_type": "submittal",
                        "resource_id": 88,
                    },
                },
            }
        )

        self.assertEqual(event.event_id, "evt-2")
        self.assertEqual(event.action, "updated")
        self.assertEqual(event.resource_type, "submittal")
        self.assertEqual(event.resource_id, "88")
        self.assertEqual(event.company_id, "456")

    def test_missing_fields_produce_warnings_not_crashes(self) -> None:
        """Sparse webhook payloads normalize with warnings."""
        event = normalize_webhook_event({"id": "evt-sparse"})

        self.assertEqual(event.event_id, "evt-sparse")
        self.assertIn("Missing event_type.", event.warnings)
        self.assertIn("Missing project_id.", event.warnings)

    def test_recursive_redaction(self) -> None:
        """Sensitive keys are redacted recursively."""
        redacted = redact_webhook_payload(
            {
                "authorization": "Bearer secret",
                "nested": {
                    "client_secret": "secret",
                    "items": [{"api_key": "key"}, {"safe": "value"}],
                },
            }
        )

        self.assertEqual(redacted["authorization"], "[REDACTED]")
        self.assertEqual(redacted["nested"]["client_secret"], "[REDACTED]")
        self.assertEqual(redacted["nested"]["items"][0]["api_key"], "[REDACTED]")
        self.assertEqual(redacted["nested"]["items"][1]["safe"], "value")

    def test_save_event_writes_original_and_normalized_files(self) -> None:
        """Saving writes both redacted original and normalized JSON files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            result = save_webhook_event(
                {
                    "event_id": "evt-save",
                    "event_type": "rfi.created",
                    "action": "created",
                    "project_id": 123,
                    "company_id": 456,
                    "resource": {"type": "rfi", "id": 99},
                    "webhook_secret": "secret",
                },
                event_dir=Path(temp_dir),
            )

            self.assertIsInstance(result, WebhookEventStoreResult)
            self.assertTrue(result.original_path.exists())
            self.assertTrue(result.normalized_path.exists())
            original = json.loads(result.original_path.read_text(encoding="utf-8"))
            normalized = json.loads(result.normalized_path.read_text(encoding="utf-8"))
            self.assertEqual(original["webhook_secret"], "[REDACTED]")
            self.assertEqual(normalized["event_id"], "evt-save")

    def test_list_events_reads_saved_events_and_filters(self) -> None:
        """Saved normalized events can be listed and filtered."""
        with tempfile.TemporaryDirectory() as temp_dir:
            event_dir = Path(temp_dir)
            save_webhook_event(
                {
                    "event_id": "evt-rfi",
                    "event_type": "rfi.created",
                    "action": "created",
                    "project_id": 123,
                    "company_id": 456,
                    "resource": {"type": "rfi", "id": 99},
                },
                event_dir=event_dir,
            )
            save_webhook_event(
                {
                    "event_id": "evt-submittal",
                    "event_type": "submittal.updated",
                    "action": "updated",
                    "project_id": 999,
                    "company_id": 456,
                    "resource": {"type": "submittal", "id": 88},
                },
                event_dir=event_dir,
            )

            all_events = list_webhook_events(event_dir=event_dir)
            filtered = list_webhook_events(
                event_dir=event_dir,
                filters={"project_id": "123", "resource_type": "rfi"},
            )

            self.assertEqual(len(all_events), 2)
            self.assertEqual([event.event_id for event in filtered], ["evt-rfi"])

    def test_dispatch_without_workflow_plan_returns_noop(self) -> None:
        """Dispatch without a workflow plan reports a no-op."""
        event = WebhookEvent(event_id="evt-noop")
        result = dispatch_webhook_event(event)

        self.assertFalse(result.dispatched)
        self.assertTrue(result.dry_run)
        self.assertIn("No workflow plan supplied", result.message)

    def test_dispatch_with_workflow_plan_uses_dry_run_and_event_placeholders(self) -> None:
        """Dispatch injects event placeholders and defaults to dry-run."""
        event = WebhookEvent(
            event_id="evt-dispatch",
            event_type="rfi.created",
            action="created",
            company_id="456",
            project_id="123",
            resource_type="rfi",
            resource_id="99",
        )
        plan = WorkflowPlan(
            name="webhook-plan",
            steps=[
                WorkflowStep(
                    id="sync",
                    workflow="sync_rfis",
                    options={"project_id": "{event.project_id}"},
                )
            ],
        )
        workflow_result = _workflow_run_result(plan)

        with patch("pyprocore.webhooks.run_workflow_plan", return_value=workflow_result) as runner:
            result = dispatch_webhook_event(event, workflow_plan=plan)

        called_plan = runner.call_args.args[0]
        self.assertTrue(result.dispatched)
        self.assertTrue(runner.call_args.kwargs["dry_run"])
        self.assertEqual(called_plan.defaults["event"]["project_id"], "123")
        self.assertEqual(called_plan.defaults["event"]["id"], "evt-dispatch")


class WebhookCliTestCase(unittest.TestCase):
    """Validate webhook command parsing and dispatch."""

    def test_cli_webhook_validate(self) -> None:
        """The validate command loads and returns a normalized event."""
        with tempfile.TemporaryDirectory() as temp_dir:
            path = _write_event(Path(temp_dir) / "event.json")
            args = app.build_parser().parse_args(["webhook", "validate", str(path)])

            result = app.run_command(args)

        self.assertIsInstance(result, WebhookEvent)
        self.assertEqual(result.event_id, "evt-cli")

    def test_cli_webhook_save(self) -> None:
        """The save command writes webhook event files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            event_path = _write_event(root / "event.json")
            args = app.build_parser().parse_args(
                ["webhook", "save", str(event_path), "--event-dir", str(root / "events")]
            )

            result = app.run_command(args)
            self.assertTrue(result.normalized_path.exists())

        self.assertIsInstance(result, WebhookEventStoreResult)

    def test_cli_webhook_list(self) -> None:
        """The list command returns saved events matching filters."""
        with tempfile.TemporaryDirectory() as temp_dir:
            event_dir = Path(temp_dir) / "events"
            save_webhook_event(_event_payload(), event_dir=event_dir)
            args = app.build_parser().parse_args(
                ["webhook", "list", "--event-dir", str(event_dir), "--project-id", "123"]
            )

            result = app.run_command(args)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].event_id, "evt-cli")

    def test_cli_webhook_dispatch_dry_run(self) -> None:
        """The dispatch command uses dry-run by default."""
        with tempfile.TemporaryDirectory() as temp_dir:
            event_path = _write_event(Path(temp_dir) / "event.json")
            plan = WorkflowPlan(
                name="webhook-plan",
                steps=[WorkflowStep(id="sync", workflow="sync_rfis")],
            )
            workflow_result = _workflow_run_result(plan)
            args = app.build_parser().parse_args(
                ["webhook", "dispatch", str(event_path), "--workflow-plan", "plan.json"]
            )

            with (
                patch("pyprocore.webhooks.load_workflow_plan", return_value=plan),
                patch(
                    "pyprocore.webhooks.run_workflow_plan",
                    return_value=workflow_result,
                ) as runner,
            ):
                result = app.run_command(args)

        self.assertTrue(result.dispatched)
        self.assertTrue(result.dry_run)
        self.assertTrue(runner.call_args.kwargs["dry_run"])


def _event_payload() -> dict[str, object]:
    """Return a representative webhook payload for tests."""
    return {
        "event_id": "evt-cli",
        "event_type": "rfi.created",
        "action": "created",
        "project_id": 123,
        "company_id": 456,
        "resource": {"type": "rfi", "id": 99},
    }


def _write_event(path: Path) -> Path:
    """Write a representative webhook payload to disk."""
    path.write_text(json.dumps(_event_payload()), encoding="utf-8")
    return path


def _workflow_run_result(plan: WorkflowPlan) -> WorkflowRunResult:
    """Build a minimal workflow run result for dispatch tests."""
    manifest = WorkflowRunManifest(
        run_id="run-test",
        plan_name=plan.name,
        status="dry_run",
        started_at="2026-07-10T00:00:00Z",
        output_dir=Path("exports/test"),
        dry_run=True,
    )
    return WorkflowRunResult(
        run_id="run-test",
        plan=plan,
        output_dir=Path("exports/test"),
        status="dry_run",
        dry_run=True,
        manifest_path=Path("exports/test/run_manifest.json"),
        summary_path=Path("exports/test/run_summary.md"),
        resolved_plan_path=Path("exports/test/plan_resolved.json"),
        manifest=manifest,
    )


if __name__ == "__main__":
    unittest.main()
