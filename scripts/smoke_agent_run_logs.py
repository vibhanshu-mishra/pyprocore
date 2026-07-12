"""Smoke-test local Agent API run logging and replay without calling Procore."""

from __future__ import annotations

import json
import shutil
import tempfile
import threading
from http.server import ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib import request
from urllib.error import HTTPError

from pyprocore.agent import create_agent_api_handler, replay_agent_run


def _read_json(url: str, *, method: str = "GET") -> tuple[int, dict[str, Any] | list[Any]]:
    """Read a JSON response from the local smoke-test server."""
    api_request = request.Request(url, method=method)
    try:
        with request.urlopen(api_request, timeout=5) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        return exc.code, json.loads(exc.read().decode("utf-8"))


def _assert(condition: bool, message: str) -> None:
    """Raise a clear smoke-test failure when a condition is false."""
    if not condition:
        raise AssertionError(message)


def main() -> int:
    """Run the local Agent API run-log smoke test."""
    temp_root = Path(tempfile.mkdtemp(prefix="pyprocore-agent-runs-"))
    run_log_dir = temp_root / "agent-runs"
    run_id = "smoke-agent-run"
    try:
        handler = create_agent_api_handler(run_log_dir=run_log_dir, run_id=run_id)
        try:
            server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        except PermissionError:
            print(
                "Agent run-log smoke test skipped: local loopback socket binding is not permitted."
            )
            return 0

        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base_url = f"http://127.0.0.1:{server.server_port}"

        try:
            for path in ("/health", "/agent/tools", "/agent/tools/procore.find_rfi"):
                status, payload = _read_json(f"{base_url}{path}")
                _assert(status == 200, f"Expected {path} to return 200.")
                _assert(payload is not None, f"Expected {path} to return JSON.")

            status, disabled = _read_json(
                f"{base_url}/agent/tools/procore.find_rfi/call",
                method="POST",
            )
            _assert(status == 501, "Expected disabled tool call to return 501.")
            _assert(isinstance(disabled, dict), "Expected disabled response object.")
            _assert(
                disabled.get("error") == "tool_execution_disabled",
                "Expected tool_execution_disabled.",
            )
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)

        run_dir = run_log_dir / run_id
        _assert((run_dir / "run.json").exists(), "Expected run.json to be created.")
        _assert((run_dir / "events.jsonl").exists(), "Expected events.jsonl to be created.")

        replay = replay_agent_run(run_log_dir, run_id)
        _assert(replay.passed, "Expected replay to pass.")
        _assert(replay.event_count >= 4, "Expected replay to include logged events.")
    finally:
        shutil.rmtree(temp_root, ignore_errors=True)

    print("Agent run-log smoke test passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
