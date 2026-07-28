"""Tests for Phase 19B read-only RFI/Submittal intake sync."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import patch

import pyprocore
from pyprocore.core.exceptions import ValidationError
from pyprocore.intake import (
    IntakeSyncConfig,
    build_initial_intake_sync_state,
    build_intake_attachment_manifest,
    build_intake_sync_config,
    build_intake_sync_plan,
    intake_run_result_to_markdown,
    intake_state_to_markdown,
    intake_to_json,
    intake_validation_to_markdown,
    load_intake_sync_config,
    load_intake_sync_state,
    normalize_rfi_record,
    normalize_submittal_record,
    render_attachment_manifest_json,
    render_attachment_manifest_markdown,
    run_intake_sync_with_records,
    save_intake_sync_state,
    summarize_intake_sync_plan,
    update_intake_sync_state_after_run,
    validate_intake_sync_config,
    write_attachment_manifest,
    write_intake_sync_config_template,
    write_intake_sync_outputs,
)

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "examples/intake"
CONFIG = FIXTURES / "intake_config.json"


def load_fixture(name: str) -> dict[str, list[dict[str, object]]]:
    """Load one project-keyed fake record fixture."""
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


class Phase19BIntakeSyncTests(unittest.TestCase):
    """Validate local-only intake planning, normalization, and outputs."""

    def run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        """Run the local CLI with credential variables removed."""
        env = {
            key: value
            for key, value in os.environ.items()
            if key
            not in {
                "PROCORE_CLIENT_ID",
                "PROCORE_CLIENT_SECRET",
                "OPENAI_API_KEY",
            }
        }
        env["PYTHONPATH"] = str(ROOT)
        return subprocess.run(
            [sys.executable, "-m", "pyprocore.app", *args],
            cwd=ROOT,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_sample_config_is_secret_free_and_root_exports_exist(self) -> None:
        """Templates should contain metadata references but no credentials."""
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "intake.json"
            write_intake_sync_config_template(path)
            text = path.read_text(encoding="utf-8")
            self.assertNotIn("client_secret", text)
            self.assertNotIn("access_token", text)
            self.assertTrue(hasattr(pyprocore, "IntakeSyncConfig"))
            self.assertTrue(hasattr(pyprocore, "run_intake_sync_with_records"))
            with self.assertRaises(ValidationError):
                write_intake_sync_config_template(path)
            write_intake_sync_config_template(path, overwrite=True)

    def test_config_validation_catches_missing_projects_and_resources(self) -> None:
        """Invalid plans should explain missing projects and resources."""
        config = IntakeSyncConfig(
            project_ids=[],
            include_rfis=False,
            include_submittals=False,
            max_items_per_project=0,
        )
        codes = {item.code for item in validate_intake_sync_config(config)}
        self.assertIn("missing_project_ids", codes)
        self.assertIn("no_resources_selected", codes)
        self.assertIn("invalid_max_items", codes)
        with self.assertRaisesRegex(ValidationError, "Invalid intake sync config"):
            run_intake_sync_with_records(config)

    def test_plan_lists_projects_resources_outputs_and_boundaries(self) -> None:
        """Planning should be deterministic, credential-free, and non-executing."""
        config = load_intake_sync_config(CONFIG)
        with patch("requests.Session.request") as request:
            plan = build_intake_sync_plan(config)
        text = summarize_intake_sync_plan(plan)
        self.assertEqual(plan.project_ids, [1001])
        self.assertEqual(plan.resources, ["rfis", "submittals"])
        self.assertIn("rfis.csv", plan.output_files)
        self.assertIn("raw/submittals_1001.json", plan.output_files)
        self.assertIn("no Procore write actions", text)
        request.assert_not_called()

    def test_config_json_restrictions(self) -> None:
        """Config helpers should reject traversal, non-JSON, and invalid JSON."""
        with self.assertRaises(ValidationError):
            write_intake_sync_config_template("../intake.json")
        with self.assertRaises(ValidationError):
            write_intake_sync_config_template("intake.yaml")
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "bad.json"
            path.write_text("{", encoding="utf-8")
            with self.assertRaises(ValidationError):
                load_intake_sync_config(path)
            path.write_text("[]", encoding="utf-8")
            with self.assertRaises(ValidationError):
                load_intake_sync_config(path)
            path.write_text('{"project_ids": "wrong"}', encoding="utf-8")
            with self.assertRaises(ValidationError):
                load_intake_sync_config(path)
            with self.assertRaises(ValidationError):
                load_intake_sync_config(Path(temp_dir) / "missing.json")
        self.assertEqual(build_intake_sync_config(project_ids=[9]).project_ids, [9])
        self.assertIn(
            "No findings",
            intake_validation_to_markdown(
                validate_intake_sync_config(IntakeSyncConfig(profile_name="ok", project_ids=[9]))
            ),
        )

    def test_state_round_trip_and_overwrite_protection(self) -> None:
        """Polling state should be local JSON with explicit replacement."""
        config = load_intake_sync_config(CONFIG)
        state = build_initial_intake_sync_state(config)
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "state.json"
            self.assertEqual(save_intake_sync_state(state, path), path.resolve())
            self.assertEqual(load_intake_sync_state(path), state)
            self.assertNotIn("secret", path.read_text(encoding="utf-8").casefold())
            with self.assertRaises(ValidationError):
                save_intake_sync_state(state, path)
            save_intake_sync_state(state, path, overwrite=True)
            with self.assertRaises(ValidationError):
                save_intake_sync_state(state, "../state.json")
            with self.assertRaises(ValidationError):
                load_intake_sync_state("../state.json")
            bad = Path(temp_dir) / "bad.json"
            bad.write_text("{", encoding="utf-8")
            with self.assertRaises(ValidationError):
                load_intake_sync_state(bad)
            bad.write_text('{"project_ids": "wrong"}', encoding="utf-8")
            with self.assertRaises(ValidationError):
                load_intake_sync_state(bad)
            with self.assertRaises(ValidationError):
                load_intake_sync_state(Path(temp_dir) / "missing.json")
        self.assertIn("contains no credentials", intake_state_to_markdown(state))

    def test_normalizers_are_tolerant_and_record_key_findings(self) -> None:
        """Sparse and unknown local payloads should not crash normalization."""
        rfi = normalize_rfi_record({"unknown": True}, 1001)
        submittal = normalize_submittal_record({"id": 3, "extra": "kept"}, 1001)
        self.assertIsNone(rfi.record.title)
        self.assertEqual(rfi.raw_record, {"unknown": True})
        self.assertEqual(
            {item.code for item in rfi.findings},
            {
                "missing_id",
                "missing_number",
                "missing_title",
            },
        )
        self.assertEqual(submittal.record.id, "3")
        self.assertIn("missing_number", {item.code for item in submittal.findings})

    def test_normalizers_support_nested_names_and_common_fields(self) -> None:
        """Common nested people/company fields should become readable strings."""
        rfi = normalize_rfi_record(
            {
                "id": 1,
                "number": "15",
                "title": "Question",
                "ball_in_court": {"name": "Engineer"},
                "assignees": [{"name": "Reviewer"}],
                "attachments": [{"name": "one.pdf"}],
            },
            1001,
        )
        submittal = normalize_submittal_record(
            {
                "id": 2,
                "number": "27",
                "title": "Shop Drawings",
                "submitter": {"name": "Fabricator"},
                "approvers": [{"name": "Engineer"}],
                "package": {"name": "Steel"},
            },
            1001,
        )
        self.assertEqual(rfi.record.ball_in_court, "Engineer")
        self.assertEqual(rfi.record.assignees, ["Reviewer"])
        self.assertEqual(rfi.record.attachment_count, 1)
        self.assertEqual(submittal.record.submitter, "Fabricator")
        self.assertEqual(submittal.record.package, "Steel")

    def test_updated_since_and_max_items_filtering(self) -> None:
        """Mocked runs should filter old records and enforce per-project limits."""
        config = load_intake_sync_config(CONFIG).model_copy(update={"max_items_per_project": 1})
        result = run_intake_sync_with_records(
            config,
            load_fixture("fake_rfis.json"),
            load_fixture("fake_submittals.json"),
        )
        rfi_result = next(item for item in result.resource_results if item.resource == "rfis")
        self.assertEqual(rfi_result.received_count, 2)
        self.assertEqual(rfi_result.included_count, 1)
        self.assertEqual(rfi_result.filtered_count, 1)
        self.assertEqual(result.summary.rfi_count, 1)
        self.assertEqual(result.summary.submittal_count, 1)

    def test_state_update_tracks_each_selected_resource(self) -> None:
        """Successful mocked runs should advance per-project polling state."""
        config = load_intake_sync_config(CONFIG)
        before = build_initial_intake_sync_state(config)
        result = run_intake_sync_with_records(
            config,
            load_fixture("fake_rfis.json"),
            load_fixture("fake_submittals.json"),
            state=before,
        )
        after = update_intake_sync_state_after_run(before, result)
        self.assertIn("1001", after.per_project_rfi_sync_at)
        self.assertIn("1001", after.per_project_submittal_sync_at)
        self.assertIsNotNone(after.last_successful_sync_at)
        self.assertEqual(after.record_counts, {"rfis": 1, "submittals": 1})

    def test_attachment_manifest_extracts_common_shapes_without_downloads(self) -> None:
        """Manifest extraction should inspect metadata but never follow URLs."""
        records = [
            (
                "rfi",
                1001,
                {
                    "id": 1,
                    "attachments": [{"filename": "a.pdf", "url": "https://invalid/a"}],
                    "attachment": {"name": "b.pdf"},
                },
            ),
            (
                "submittal",
                1001,
                {"id": 2, "files": [{"name": "c.pdf"}], "documents": [{"id": 4}]},
            ),
        ]
        with patch("requests.Session.get") as get:
            manifest = build_intake_attachment_manifest(records)  # type: ignore[arg-type]
        self.assertEqual(len(manifest.items), 4)
        self.assertTrue(manifest.items[0].download_available)
        self.assertIn("DMSA permissions", manifest.note)
        self.assertIn("does not download", render_attachment_manifest_json(manifest))
        self.assertIn("URL present", render_attachment_manifest_markdown(manifest))
        get.assert_not_called()

    def test_attachment_manifest_writers_are_local_and_protected(self) -> None:
        """JSON/Markdown writers should enforce extension, containment, and overwrite."""
        manifest = build_intake_attachment_manifest([])
        self.assertIn("No attachment metadata", render_attachment_manifest_markdown(manifest))
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir).resolve()
            json_path = root / "manifest.json"
            md_path = root / "manifest.md"
            self.assertEqual(
                write_attachment_manifest(
                    manifest,
                    json_path,
                    output_root=root,
                ),
                json_path,
            )
            write_attachment_manifest(manifest, md_path, output_root=root)
            self.assertIn('"items": []', json_path.read_text(encoding="utf-8"))
            self.assertIn("Intake Attachment Manifest", md_path.read_text(encoding="utf-8"))
            with self.assertRaises(ValidationError):
                write_attachment_manifest(manifest, json_path, output_root=root)
            write_attachment_manifest(
                manifest,
                json_path,
                output_root=root,
                overwrite=True,
            )
            with self.assertRaises(ValidationError):
                write_attachment_manifest(manifest, root / "manifest.txt")
            with self.assertRaises(ValidationError):
                write_attachment_manifest(manifest, "../manifest.json")
            with self.assertRaises(ValidationError):
                write_attachment_manifest(
                    manifest,
                    root.parent / "outside.json",
                    output_root=root,
                )

    def test_mocked_sync_summary_and_empty_findings(self) -> None:
        """Mocked execution should report counts, findings, and strict safety flags."""
        config = load_intake_sync_config(CONFIG)
        result = run_intake_sync_with_records(config, {}, {})
        codes = {item.code for item in result.findings}
        self.assertIn("empty_resource", codes)
        self.assertFalse(result.summary.procore_calls_made)
        self.assertFalse(result.summary.remote_downloads_made)
        self.assertFalse(result.summary.write_actions_enabled)
        markdown = intake_run_result_to_markdown(result)
        self.assertIn("mocked/local records only", markdown)
        self.assertIn("empty_resource", markdown)

    def test_output_dry_run_lists_files_without_writing(self) -> None:
        """Dry-run should return planned paths and create nothing."""
        config = load_intake_sync_config(CONFIG)
        result = run_intake_sync_with_records(
            config,
            load_fixture("fake_rfis.json"),
            load_fixture("fake_submittals.json"),
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "not-created"
            manifest = write_intake_sync_outputs(result, root, dry_run=True)
            self.assertTrue(manifest.dry_run)
            self.assertIn("rfis.csv", manifest.planned_files)
            self.assertFalse(root.exists())

    def test_output_writer_creates_expected_local_formats_and_raw_json(self) -> None:
        """Explicit local writes should remain contained and preserve raw records."""
        config = load_intake_sync_config(CONFIG)
        result = run_intake_sync_with_records(
            config,
            load_fixture("fake_rfis.json"),
            load_fixture("fake_submittals.json"),
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "outputs"
            manifest = write_intake_sync_outputs(result, root, dry_run=False)
            self.assertFalse(manifest.dry_run)
            for relative in (
                "rfis.csv",
                "rfis.jsonl",
                "submittals.csv",
                "raw/rfis_1001.json",
                "state/intake_state.json",
                "output_manifest.json",
            ):
                self.assertTrue((root / relative).is_file())
            rfi_jsonl = (root / "rfis.jsonl").read_text(encoding="utf-8")
            self.assertIn('"number": "RFI-015"', rfi_jsonl)
            self.assertIn("RFI-015", (root / "rfis.csv").read_text(encoding="utf-8"))
            raw = json.loads((root / "raw/rfis_1001.json").read_text(encoding="utf-8"))
            self.assertEqual(raw[0]["id"], 501)
            with self.assertRaises(ValidationError):
                write_intake_sync_outputs(result, root, dry_run=False)
            write_intake_sync_outputs(
                result,
                root,
                dry_run=False,
                overwrite=True,
            )

    def test_output_path_traversal_is_blocked(self) -> None:
        """Output roots and planned child paths must stay contained."""
        config = load_intake_sync_config(CONFIG)
        result = run_intake_sync_with_records(config, {}, {})
        with self.assertRaises(ValidationError):
            write_intake_sync_outputs(result, "../outside", dry_run=True)
        unsafe = result.model_copy(deep=True)
        unsafe.plan.output_files.append("../escape.json")
        with tempfile.TemporaryDirectory() as temp_dir:
            with self.assertRaises(ValidationError):
                write_intake_sync_outputs(unsafe, temp_dir, dry_run=True)

    def test_optional_resource_plans_and_empty_csv_outputs(self) -> None:
        """Single-resource plans and empty CSV files should remain valid."""
        config = IntakeSyncConfig(
            profile_name="local",
            project_ids=[1001],
            include_rfis=False,
            include_submittals=True,
            include_attachments=False,
            dry_run=False,
        )
        plan = build_intake_sync_plan(config)
        self.assertNotIn("rfis.csv", plan.output_files)
        self.assertNotIn("attachments_manifest.json", plan.output_files)
        result = run_intake_sync_with_records(config, {}, {"1001": []})
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "outputs"
            write_intake_sync_outputs(result, root, dry_run=False)
            self.assertEqual((root / "submittals.csv").read_text(encoding="utf-8"), "")

    def test_cli_commands_work_without_credentials(self) -> None:
        """All Phase 19B commands should operate entirely on local files."""
        commands = [
            ("intake", "validate-config", str(CONFIG), "--format", "json"),
            ("intake", "plan", str(CONFIG), "--format", "markdown"),
            (
                "intake",
                "run-mock",
                str(CONFIG),
                "--rfis",
                str(FIXTURES / "fake_rfis.json"),
                "--submittals",
                str(FIXTURES / "fake_submittals.json"),
                "--format",
                "json",
            ),
            (
                "intake",
                "attachment-manifest",
                str(FIXTURES / "fake_attachment_records.json"),
            ),
            ("intake", "state", "show", str(FIXTURES / "fake_state.json")),
        ]
        for command in commands:
            with self.subTest(command=command):
                completed = self.run_cli(*command)
                self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
                self.assertNotIn("Traceback", completed.stdout + completed.stderr)

    def test_cli_sample_state_and_mock_write_dry_run(self) -> None:
        """File-oriented CLI commands should honor overwrite and dry-run behavior."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            config_path = root / "config.json"
            state_path = root / "state.json"
            sample = self.run_cli(
                "intake",
                "sample-config",
                "--output",
                str(config_path),
            )
            self.assertEqual(sample.returncode, 0, sample.stderr)
            state = self.run_cli(
                "intake",
                "state",
                "init",
                "--output",
                str(state_path),
                "--config",
                str(CONFIG),
            )
            self.assertEqual(state.returncode, 0, state.stderr)
            output = root / "dry-output"
            dry_run = self.run_cli(
                "intake",
                "write-mock",
                str(CONFIG),
                "--rfis",
                str(FIXTURES / "fake_rfis.json"),
                "--submittals",
                str(FIXTURES / "fake_submittals.json"),
                "--output-dir",
                str(output),
                "--dry-run",
            )
            self.assertEqual(dry_run.returncode, 0, dry_run.stderr)
            self.assertFalse(output.exists())

    def test_examples_run_without_credentials_or_network(self) -> None:
        """Examples 341-346 should be deterministic local demonstrations."""
        for number in range(341, 347):
            example = next(ROOT.glob(f"examples/{number}_*.py"))
            completed = subprocess.run(
                [sys.executable, str(example)],
                cwd=ROOT,
                env={"PYTHONPATH": str(ROOT), "PATH": os.environ.get("PATH", "")},
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(
                completed.returncode,
                0,
                f"{example.name}: {completed.stderr}",
            )

    def test_safety_boundaries_and_dependency_surface(self) -> None:
        """Phase 19B must stay local, read-only, and dependency-neutral."""
        sources = "\n".join(
            path.read_text(encoding="utf-8") for path in (ROOT / "pyprocore/intake").glob("*.py")
        ).casefold()
        forbidden = (
            "requests.get(",
            "requests.post(",
            "session.get(",
            "openai",
            "mcp execution",
            "create_rfi",
            "update_rfi",
            "delete_rfi",
            "approve_submittal",
        )
        for phrase in forbidden:
            self.assertNotIn(phrase, sources)
        pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        self.assertNotIn("intake-sync", pyproject)
        self.assertEqual(pyprocore.__version__, "2.4.0")

    def test_intake_docs_preserve_access_and_safety_truth(self) -> None:
        """Public intake docs should retain the Phase 19B product boundary."""
        text = (ROOT / "docs/rfi-submittal-intake-sync.md").read_text(encoding="utf-8")
        text_lower = text.casefold()
        for phrase in (
            "read-only",
            "gc/owner",
            "does not grant access",
            "rfi",
            "submittal",
            "attachment",
            "no procore write actions",
            "mocked/local",
        ):
            self.assertIn(phrase, text_lower)
        self.assertIn("does not download remote attachments", text_lower)

    def test_state_serialization_contains_no_secret_fields(self) -> None:
        """State and summary serialization should not expose credential fields."""
        config = load_intake_sync_config(CONFIG)
        result = run_intake_sync_with_records(config, {}, {})
        text = intake_to_json(result.state_after).casefold()
        for marker in ("client_secret", "access_token", "refresh_token", "authorization"):
            self.assertNotIn(marker, text)
        self.assertIsInstance(result.summary.started_at, datetime)
        self.assertIsNotNone(result.summary.started_at.tzinfo)
        self.assertEqual(result.summary.started_at.tzinfo, UTC)


if __name__ == "__main__":
    unittest.main()
