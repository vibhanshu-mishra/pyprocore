"""Tests for local Agent API run logs and replay."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from io import BytesIO
from pathlib import Path
from typing import Any
from unittest.mock import patch

from pyprocore import app
from pyprocore.agent import (
    AgentReplayResult,
    AgentRun,
    AgentRunEvent,
    AgentRunLogStore,
    append_agent_run_event,
    create_agent_api_handler,
    create_agent_run,
    export_agent_run_bundle,
    list_agent_runs,
    load_agent_run,
    redact_agent_event_payload,
    replay_agent_run,
)
from pyprocore.agent import runs as agent_runs_module
from pyprocore.agent import server as agent_server_module

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def dispatch_handler(
    path: str,
    *,
    handler_cls: type[Any] | None = None,
    method: str = "GET",
) -> tuple[int, dict[str, str], dict[str, Any] | list[Any]]:
    """Dispatch the local handler without opening a socket."""
    active_handler_cls = handler_cls or create_agent_api_handler()
    handler = active_handler_cls.__new__(active_handler_cls)
    handler.path = path
    handler.command = method
    handler.wfile = BytesIO()

    captured_status = 0
    captured_headers: dict[str, str] = {}

    def send_response(status: int) -> None:
        nonlocal captured_status
        captured_status = status

    def send_header(name: str, value: str) -> None:
        captured_headers[name] = value

    handler.send_response = send_response  # type: ignore[method-assign]
    handler.send_header = send_header  # type: ignore[method-assign]
    handler.end_headers = lambda: None  # type: ignore[method-assign]

    if method == "GET":
        handler.do_GET()
    elif method == "POST":
        handler.do_POST()
    else:
        raise AssertionError(f"Unsupported test method: {method}")

    payload = json.loads(handler.wfile.getvalue().decode("utf-8"))
    return captured_status, captured_headers, payload


class AgentRunLogsTestCase(unittest.TestCase):
    """Validate local Agent API run logging and replay."""

    def test_run_models_exist(self) -> None:
        """Run log models should be importable and constructable."""
        self.assertEqual(AgentRunLogStore().root_dir, Path("agent-runs"))
        self.assertTrue(AgentRun)
        self.assertTrue(AgentRunEvent)
        self.assertTrue(AgentReplayResult)

    def test_create_append_load_and_list_run(self) -> None:
        """Run helpers should write and read local JSON and JSONL files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            run = create_agent_run(temp_dir, run_id="test-run", metadata={"source": "unit"})
            event = append_agent_run_event(
                temp_dir,
                run.run_id,
                method="GET",
                path="/health",
                status_code=200,
                event_type="health",
                response_summary={"status": "ok"},
            )
            loaded = load_agent_run(temp_dir, run.run_id)
            runs = list_agent_runs(temp_dir)

            self.assertEqual(run.run_id, "test-run")
            self.assertEqual(event.run_id, "test-run")
            self.assertEqual(len(loaded.events), 1)
            self.assertEqual(runs[0].run_id, "test-run")
            self.assertTrue((Path(temp_dir) / "test-run" / "events.jsonl").exists())

    def test_replay_run_passes_and_does_not_execute_tools(self) -> None:
        """Replay should verify logged events without executing tools."""
        with tempfile.TemporaryDirectory() as temp_dir:
            run = create_agent_run(temp_dir, run_id="replay-run")
            append_agent_run_event(
                temp_dir,
                run.run_id,
                method="POST",
                path="/agent/tools/procore.find_rfi/call",
                tool_name="procore.find_rfi",
                status_code=501,
                event_type="tool_execution_disabled",
                response_summary={"error": "tool_execution_disabled"},
                error_type="tool_execution_disabled",
            )
            with patch("pyprocore.core.config.get_settings") as get_settings:
                replay = replay_agent_run(temp_dir, run.run_id)

            get_settings.assert_not_called()
            self.assertTrue(replay.passed)
            self.assertEqual(replay.event_count, 1)

    def test_replay_warns_on_unknown_tool(self) -> None:
        """Replay should warn when an old run references an unknown tool."""
        with tempfile.TemporaryDirectory() as temp_dir:
            run = create_agent_run(temp_dir, run_id="unknown-tool-run")
            append_agent_run_event(
                temp_dir,
                run.run_id,
                method="GET",
                path="/agent/tools/procore.missing",
                tool_name="procore.missing",
                status_code=404,
                event_type="tool_not_found",
                response_summary={"error": "tool_not_found"},
                error_type="tool_not_found",
            )

            replay = replay_agent_run(temp_dir, run.run_id)

            self.assertTrue(replay.passed)
            self.assertTrue(
                any("Unknown registered tool" in warning for warning in replay.warnings)
            )

    def test_redaction_removes_sensitive_values(self) -> None:
        """Redaction should remove token-like and signed URL values."""
        payload = {
            "Authorization": "Bearer secret",
            "client_secret": "secret",
            "url": "https://example.com/file.pdf?Signature=abc&Expires=123",
            "nested": {"access_token": "token"},
        }

        redacted = redact_agent_event_payload(payload)

        self.assertEqual(redacted["Authorization"], "[REDACTED]")
        self.assertEqual(redacted["client_secret"], "[REDACTED]")
        self.assertEqual(redacted["nested"]["access_token"], "[REDACTED]")
        self.assertIn("Signature=[REDACTED]", redacted["url"])

    def test_server_logging_disabled_by_default(self) -> None:
        """The server should not write logs unless explicitly enabled."""
        with tempfile.TemporaryDirectory() as temp_dir:
            dispatch_handler("/health")

            self.assertEqual(list(Path(temp_dir).glob("*")), [])

    def test_server_logging_writes_files_when_enabled(self) -> None:
        """The server should append events when run logging is enabled."""
        with tempfile.TemporaryDirectory() as temp_dir:
            handler_cls = create_agent_api_handler(run_log_dir=temp_dir, run_id="server-run")
            dispatch_handler("/health", handler_cls=handler_cls)
            dispatch_handler(
                "/agent/tools/procore.find_rfi/call", handler_cls=handler_cls, method="POST"
            )

            loaded = load_agent_run(temp_dir, "server-run")
            replay = replay_agent_run(temp_dir, "server-run")

            self.assertEqual(len(loaded.events), 2)
            self.assertTrue(replay.passed)
            self.assertEqual(loaded.events[-1].error_type, "tool_execution_disabled")

    def test_cli_includes_agent_runs_commands(self) -> None:
        """The CLI parser should include agent runs commands."""
        parser = app.build_parser()
        args = parser.parse_args(
            ["agent", "runs", "replay", "run-1", "--run-log-dir", "agent-runs"]
        )

        self.assertEqual(args.command, "agent")
        self.assertEqual(args.agent_command, "runs")
        self.assertEqual(args.agent_runs_command, "replay")

    def test_run_command_agent_runs_branches(self) -> None:
        """Direct CLI dispatch should cover run-log commands."""
        parser = app.build_parser()
        with tempfile.TemporaryDirectory() as temp_dir:
            run = create_agent_run(temp_dir, run_id="dispatch-run")
            append_agent_run_event(
                temp_dir,
                run.run_id,
                method="GET",
                path="/health",
                status_code=200,
                event_type="health",
                response_summary={"status": "ok"},
            )

            listed = app.run_command(
                parser.parse_args(["agent", "runs", "list", "--run-log-dir", temp_dir])
            )
            shown = app.run_command(
                parser.parse_args(
                    ["agent", "runs", "show", "dispatch-run", "--run-log-dir", temp_dir]
                )
            )
            replayed = app.run_command(
                parser.parse_args(
                    ["agent", "runs", "replay", "dispatch-run", "--run-log-dir", temp_dir]
                )
            )
            exported = app.run_command(
                parser.parse_args(
                    [
                        "agent",
                        "runs",
                        "export",
                        "dispatch-run",
                        "--run-log-dir",
                        temp_dir,
                        "--output-dir",
                        str(Path(temp_dir) / "bundles"),
                    ]
                )
            )

            self.assertEqual(listed[0].run_id, "dispatch-run")
            self.assertEqual(shown.run_id, "dispatch-run")
            self.assertTrue(replayed.passed)
            self.assertTrue((exported / "replay.json").exists())

    def test_format_agent_run_outputs(self) -> None:
        """Human-readable run formatters should summarize local replay data."""
        with tempfile.TemporaryDirectory() as temp_dir:
            run = create_agent_run(temp_dir, run_id="format-run")
            replay = replay_agent_run(temp_dir, run.run_id)

            self.assertIn("No local Agent API runs", app.format_agent_runs([]))
            self.assertIn("format-run", app.format_agent_runs([run]))
            self.assertIn("Local Agent API run", app.format_agent_run(run))
            self.assertIn("Agent run replay complete", app.format_agent_replay_result(replay))

    def test_cli_run_replay_and_export_work(self) -> None:
        """CLI replay and export should work against local temp runs."""
        with tempfile.TemporaryDirectory() as temp_dir:
            run = create_agent_run(temp_dir, run_id="cli-run")
            append_agent_run_event(
                temp_dir,
                run.run_id,
                method="GET",
                path="/health",
                status_code=200,
                event_type="health",
                response_summary={"status": "ok"},
            )
            replay = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pyprocore.app",
                    "agent",
                    "runs",
                    "replay",
                    "cli-run",
                    "--run-log-dir",
                    temp_dir,
                ],
                cwd=PROJECT_ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(replay.returncode, 0, replay.stderr)
            self.assertIn("Passed: True", replay.stdout)

            bundle = export_agent_run_bundle(temp_dir, "cli-run", Path(temp_dir) / "bundles")
            self.assertTrue((bundle / "replay.json").exists())

    def test_run_helpers_cover_error_and_warning_branches(self) -> None:
        """Run helpers should handle missing files, empty runs, and invalid events."""
        with tempfile.TemporaryDirectory() as temp_dir:
            self.assertEqual(list_agent_runs(Path(temp_dir) / "missing"), [])
            with self.assertRaises(FileNotFoundError):
                load_agent_run(temp_dir, "missing")
            with self.assertRaises(FileNotFoundError):
                append_agent_run_event(
                    temp_dir,
                    "missing",
                    method="GET",
                    path="/health",
                    status_code=200,
                    event_type="health",
                )
            with self.assertRaises(ValueError):
                agent_runs_module.sanitize_run_id("...")

            run = create_agent_run(temp_dir, run_id="empty-run")
            replay = replay_agent_run(temp_dir, run.run_id)
            self.assertIn("no events", replay.warnings[0])

            append_agent_run_event(
                temp_dir,
                run.run_id,
                method="",
                path="/unknown",
                status_code=0,
                event_type="bad",
            )
            invalid_replay = replay_agent_run(temp_dir, run.run_id)
            self.assertFalse(invalid_replay.passed)
            self.assertTrue(invalid_replay.errors)
            self.assertTrue(invalid_replay.warnings)

    def test_server_private_helpers_and_run_server_wrapper(self) -> None:
        """Server helper branches should stay deterministic and local."""
        self.assertIsNone(agent_server_module._tool_name_from_path("/health"))
        self.assertEqual(
            agent_server_module._tool_name_from_path("/agent/tools/procore.find_rfi/call"),
            "procore.find_rfi",
        )
        self.assertEqual(
            agent_server_module._event_type_from_path(
                "/agent/tools/procore.find_rfi/call", 500, None
            ),
            "tool_call",
        )
        self.assertEqual(agent_server_module._event_type_from_path("/", 200, None), "root")
        self.assertEqual(
            agent_server_module._event_type_from_path("/missing", 404, None), "not_found"
        )
        self.assertEqual(agent_server_module._response_summary([{"a": 1}])["count"], 1)
        self.assertEqual(agent_server_module._response_summary({"tool_count": 2})["tool_count"], 2)

        class FakeServer:
            """Short-lived fake HTTP server for wrapper coverage."""

            server_port = 8765

            def __init__(self, address: object, handler: object) -> None:
                self.address = address
                self.handler = handler
                self.closed = False

            def serve_forever(self) -> None:
                raise KeyboardInterrupt

            def server_close(self) -> None:
                self.closed = True

        with tempfile.TemporaryDirectory() as temp_dir:
            with patch("pyprocore.agent.server.ThreadingHTTPServer", FakeServer):
                agent_server_module.run_agent_api_server(run_log_dir=temp_dir, run_id="wrapper-run")

    def test_smoke_examples_and_docs_exist(self) -> None:
        """Phase 7D smoke script, examples, and docs should be present."""
        for relative_path in (
            "scripts/smoke_agent_run_logs.py",
            "examples/58_agent_run_logs.py",
            "examples/59_replay_agent_run.py",
            "docs/recipes/inspect-agent-run-logs.md",
            "docs/recipes/replay-agent-run.md",
        ):
            self.assertTrue((PROJECT_ROOT / relative_path).exists(), relative_path)

        docs = (PROJECT_ROOT / "docs/agent-api.md").read_text(encoding="utf-8")
        mkdocs = (PROJECT_ROOT / "mkdocs.yml").read_text(encoding="utf-8")
        self.assertIn("opt-in", docs)
        self.assertIn("local run logs", docs)
        self.assertIn("inspect-agent-run-logs.md", mkdocs)
        self.assertIn("replay-agent-run.md", mkdocs)

    def test_run_log_code_does_not_call_live_api_or_enable_execution(self) -> None:
        """Run-log code should not call Procore or enable tool execution."""
        source = "\n".join(
            [
                (PROJECT_ROOT / "pyprocore/agent/runs.py").read_text(encoding="utf-8"),
                (PROJECT_ROOT / "scripts/smoke_agent_run_logs.py").read_text(encoding="utf-8"),
            ]
        )

        self.assertNotIn("requests.", source)
        self.assertNotIn("Session(", source)
        self.assertNotIn("api.procore.com", source)
        self.assertNotIn("execute_tool", source)


if __name__ == "__main__":
    unittest.main()
