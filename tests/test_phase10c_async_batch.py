"""Tests for Phase 10C async batch and multi-project helpers."""

from __future__ import annotations

import asyncio
import csv
import json
import tempfile
import unittest
from argparse import Namespace
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pyprocore
from pyprocore.app import main, run_command
from pyprocore.core.exceptions import ValidationError
from pyprocore.workflows import async_batch as async_batch_module
from pyprocore.workflows.async_batch import (
    AsyncBatchManifest,
    AsyncBatchPlan,
    AsyncBatchResourceResult,
    async_batch_manifest_to_json,
    async_collect_multi_project_documents,
    async_collect_multi_project_drawings,
    async_collect_multi_project_rfis,
    async_collect_multi_project_specifications,
    async_collect_multi_project_submittals,
    async_export_multi_project_core_resources,
    async_export_multi_project_documents,
    async_export_multi_project_drawings,
    async_export_multi_project_resources,
    async_export_multi_project_rfis,
    async_export_multi_project_specification_sections,
    async_export_multi_project_submittals,
    async_run_project_batch,
    build_async_batch_dry_run_manifest,
    build_async_batch_plan,
    explain_async_batch_plan,
    load_async_batch_plan,
    sample_async_batch_plan_json,
    validate_async_batch_plan,
    write_async_batch_manifest,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]


class FakeAsyncClient:
    """Async client double that returns deterministic records."""

    def __init__(self, *, fail_project: int | None = None, delay: float = 0) -> None:
        """Initialize the fake client."""
        self.fail_project = fail_project
        self.delay = delay
        self.active = 0
        self.max_active = 0
        self.calls: list[tuple[str, int]] = []

    async def _records(
        self, resource: str, company_id: int, project_id: int
    ) -> list[dict[str, Any]]:
        """Return fake records or raise a configured failure."""
        self.active += 1
        self.max_active = max(self.max_active, self.active)
        if self.delay:
            await asyncio.sleep(self.delay)
        self.calls.append((resource, project_id))
        self.active -= 1
        if self.fail_project == project_id:
            raise RuntimeError(
                "access_token=secret refresh_token=secret "
                "https://signed.example.com/file.pdf?token=secret"
            )
        return [{"id": project_id, "company_id": company_id, "resource": resource}]

    async def list_rfis(self, company_id: int, project_id: int, **_: Any) -> list[dict[str, Any]]:
        """Return fake RFIs."""
        return await self._records("rfis", company_id, project_id)

    async def list_submittals(
        self, company_id: int, project_id: int, **_: Any
    ) -> list[dict[str, Any]]:
        """Return fake submittals."""
        return await self._records("submittals", company_id, project_id)

    async def list_documents(
        self, company_id: int, project_id: int, **_: Any
    ) -> list[dict[str, Any]]:
        """Return fake documents."""
        return await self._records("documents", company_id, project_id)

    async def list_drawings(
        self, company_id: int, project_id: int, **_: Any
    ) -> list[dict[str, Any]]:
        """Return fake drawings."""
        return await self._records("drawings", company_id, project_id)

    async def list_specification_sections(
        self, company_id: int, project_id: int, **_: Any
    ) -> list[dict[str, Any]]:
        """Return fake specification sections."""
        return await self._records("specification_sections", company_id, project_id)


class Phase10CAsyncBatchModelTests(unittest.TestCase):
    """Validate async batch plan parsing and local dry-runs."""

    def test_async_batch_plan_parses_sample_configs(self) -> None:
        """Sample configs should parse to typed plans with placeholder IDs."""
        for name in (
            "async_batch_multi_project.json",
            "async_batch_dry_run.json",
            "async_batch_enterprise_export.json",
        ):
            plan = load_async_batch_plan(PROJECT_ROOT / "examples" / "configs" / name)
            self.assertIsInstance(plan, AsyncBatchPlan)
            self.assertEqual(plan.company_id, 12345)
            self.assertTrue(plan.dry_run)

    def test_unknown_resource_is_rejected(self) -> None:
        """Unsupported resources should produce validation errors."""
        plan = build_async_batch_plan(
            company_id=12345,
            project_ids=[67890],
            resources=["rfis", "payments"],
        )
        findings = validate_async_batch_plan(plan)
        self.assertIn("unknown_resource", [finding.code for finding in findings])

    def test_invalid_plan_file_inputs_raise_validation_errors(self) -> None:
        """Plan loader should give clear validation errors for local file mistakes."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            text_plan = temp_path / "plan.txt"
            text_plan.write_text("{}", encoding="utf-8")
            missing_plan = temp_path / "missing.json"
            invalid_json = temp_path / "invalid.json"
            invalid_json.write_text("{", encoding="utf-8")
            list_json = temp_path / "list.json"
            list_json.write_text("[]", encoding="utf-8")

            for path in (text_plan, missing_plan, invalid_json, list_json):
                with self.assertRaises(ValidationError):
                    load_async_batch_plan(path)

    def test_validation_covers_required_fields_and_output_safety(self) -> None:
        """Validation should flag unsafe or incomplete local plans."""
        plan = AsyncBatchPlan(
            plan_name="invalid",
            company_id=0,
            project_ids=[],
            resources=[],
            max_concurrency=0,
        )
        plan.output_format = "pdf"  # type: ignore[assignment]
        codes = [finding.code for finding in validate_async_batch_plan(plan)]

        self.assertIn("invalid_company_id", codes)
        self.assertIn("missing_project_ids", codes)
        self.assertIn("missing_resources", codes)
        self.assertIn("unknown_output_format", codes)
        self.assertIn("invalid_concurrency", codes)

    def test_validation_warns_for_parent_directory_output(self) -> None:
        """Parent-directory output paths should warn but remain local."""
        plan = build_async_batch_plan(
            company_id=12345,
            project_ids=[67890],
            resources=["rfis"],
            output_dir=Path("..") / "exports",
        )

        codes = [finding.code for finding in validate_async_batch_plan(plan)]
        self.assertIn("parent_directory_output", codes)

    def test_broad_scope_and_high_concurrency_warn(self) -> None:
        """Large plans and high concurrency should warn conservatively."""
        plan = build_async_batch_plan(
            company_id=12345,
            project_ids=list(range(100, 110)),
            resources=["rfis", "submittals", "documents"],
            max_concurrency=20,
        )
        codes = [finding.code for finding in validate_async_batch_plan(plan)]
        self.assertIn("broad_async_batch", codes)
        self.assertIn("high_concurrency", codes)

    def test_dry_run_manifest_generation_does_not_write_files(self) -> None:
        """Dry-run manifests should describe paths without creating exports."""
        with tempfile.TemporaryDirectory() as temp_dir:
            plan = build_async_batch_plan(
                company_id=12345,
                project_ids=[67890],
                resources=["rfis", "submittals"],
                output_dir=Path(temp_dir) / "exports",
                dry_run=True,
            )
            manifest = build_async_batch_dry_run_manifest(plan)

            self.assertIsInstance(manifest, AsyncBatchManifest)
            self.assertTrue(manifest.dry_run)
            self.assertEqual(len(manifest.results), 2)
            self.assertFalse((Path(temp_dir) / "exports").exists())

    def test_dry_run_explanation_includes_findings(self) -> None:
        """Dry-run explanation should include validation findings."""
        plan = build_async_batch_plan(
            company_id=12345,
            project_ids=[67890],
            resources=["rfis"],
            max_concurrency=20,
        )

        explanation = explain_async_batch_plan(plan)

        self.assertIn("Safety notes:", explanation)
        self.assertIn("WARNING:", explanation)
        self.assertIn("Max concurrency", explanation)

    def test_output_paths_stay_inside_output_dir(self) -> None:
        """Planned output paths should stay inside the configured output root."""
        with tempfile.TemporaryDirectory() as temp_dir:
            plan = build_async_batch_plan(
                company_id=12345,
                project_ids=[67890],
                resources=["rfis"],
                output_dir=Path(temp_dir) / "safe",
            )
            manifest = build_async_batch_dry_run_manifest(plan)
            output_path = manifest.results[0].output_path
            self.assertIsNotNone(output_path)
            self.assertTrue(
                output_path.resolve().is_relative_to((Path(temp_dir) / "safe").resolve())
            )

    def test_output_paths_can_include_timestamp_placeholder_without_files(self) -> None:
        """Timestamped plans should describe timestamp folders in dry-run paths."""
        with tempfile.TemporaryDirectory() as temp_dir:
            plan = build_async_batch_plan(
                company_id=12345,
                project_ids=[67890],
                resources=["rfis"],
                output_dir=Path(temp_dir) / "safe",
                include_timestamp=True,
            )
            manifest = build_async_batch_dry_run_manifest(plan)
            output_path = manifest.results[0].output_path

            self.assertIsNotNone(output_path)
            self.assertIn("{timestamp}", str(output_path))

    def test_manifest_serialization_excludes_in_memory_records(self) -> None:
        """Manifest JSON should not include collected in-memory records."""
        manifest = build_async_batch_dry_run_manifest(
            build_async_batch_plan(company_id=12345, project_ids=[67890], resources=["rfis"])
        )
        manifest.results[0].records = [{"url": "https://signed.example/file.pdf?token=secret"}]
        serialized = async_batch_manifest_to_json(manifest)

        self.assertIn("rfis", serialized)
        self.assertNotIn("signed.example", serialized)

    def test_manifest_write_and_compact_json(self) -> None:
        """Manifest helpers should write local JSON and support compact output."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest = build_async_batch_dry_run_manifest(
                build_async_batch_plan(company_id=12345, project_ids=[67890], resources=["rfis"])
            )
            output_path = write_async_batch_manifest(manifest, Path(temp_dir) / "manifest.json")
            compact = async_batch_manifest_to_json(manifest, pretty=False)

            self.assertTrue(output_path.exists())
            self.assertIn('"plan_name"', compact)
            self.assertNotIn("\n  ", compact)

    def test_sample_config_json_is_placeholder_only(self) -> None:
        """Sample JSON should not contain secrets."""
        sample = sample_async_batch_plan_json()
        self.assertIn("12345", sample)
        self.assertNotIn("client_secret", sample.lower())
        self.assertNotIn("access_token", sample.lower())


class Phase10CAsyncBatchRuntimeTests(unittest.IsolatedAsyncioTestCase):
    """Validate async batch runtime behavior with fake clients only."""

    async def test_multi_project_rfi_export_writes_jsonl(self) -> None:
        """Multi-project RFI export should write local JSONL files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest = await async_export_multi_project_rfis(
                FakeAsyncClient(),  # type: ignore[arg-type]
                company_id=12345,
                project_ids=[67890, 11111],
                output_dir=temp_dir,
                output_format="jsonl",
            )

            self.assertEqual(manifest.completed_count, 2)
            for result in manifest.results:
                self.assertTrue(result.output_path.exists())
                self.assertIn("resource", result.output_path.read_text(encoding="utf-8"))

    async def test_multi_project_submittal_export_writes_csv(self) -> None:
        """Multi-project submittal export should write CSV files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest = await async_export_multi_project_submittals(
                FakeAsyncClient(),  # type: ignore[arg-type]
                company_id=12345,
                project_ids=[67890],
                output_dir=temp_dir,
                output_format="csv",
            )

            output_path = manifest.results[0].output_path
            self.assertIsNotNone(output_path)
            with output_path.open(encoding="utf-8") as file_handle:
                rows = list(csv.DictReader(file_handle))
            self.assertEqual(rows[0]["resource"], "submittals")

    async def test_multi_project_document_export_uses_document_helper(self) -> None:
        """Document helper should export documents across projects."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest = await async_export_multi_project_documents(
                FakeAsyncClient(),  # type: ignore[arg-type]
                company_id=12345,
                project_ids=[67890],
                output_dir=temp_dir,
            )

            self.assertEqual(manifest.resources, ["documents"])
            self.assertEqual(manifest.completed_count, 1)

    async def test_multi_project_drawing_and_specification_exports(self) -> None:
        """Drawing and specification helpers should export their respective resources."""
        with tempfile.TemporaryDirectory() as temp_dir:
            drawings = await async_export_multi_project_drawings(
                FakeAsyncClient(),  # type: ignore[arg-type]
                company_id=12345,
                project_ids=[67890],
                output_dir=Path(temp_dir) / "drawings",
            )
            specs = await async_export_multi_project_specification_sections(
                FakeAsyncClient(),  # type: ignore[arg-type]
                company_id=12345,
                project_ids=[67890],
                output_dir=Path(temp_dir) / "specs",
            )

            self.assertEqual(drawings.resources, ["drawings"])
            self.assertEqual(specs.resources, ["specification_sections"])
            self.assertTrue(drawings.results[0].output_path.exists())
            self.assertTrue(specs.results[0].output_path.exists())

    async def test_core_resource_export_helper_includes_all_supported_resources(self) -> None:
        """Core resource helper should build the expected five-resource batch."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest = await async_export_multi_project_core_resources(
                FakeAsyncClient(),  # type: ignore[arg-type]
                company_id=12345,
                project_ids=[67890],
                output_dir=temp_dir,
            )

            self.assertEqual(manifest.completed_count, 5)
            self.assertEqual(
                set(manifest.resources),
                {"rfis", "submittals", "documents", "drawings", "specification_sections"},
            )

    async def test_collect_helpers_return_records_without_files(self) -> None:
        """Collection helpers should preserve records in memory and avoid file output."""
        manifest = await async_collect_multi_project_documents(
            FakeAsyncClient(),  # type: ignore[arg-type]
            company_id=12345,
            project_ids=[67890],
        )

        self.assertEqual(manifest.completed_count, 1)
        self.assertEqual(manifest.results[0].records[0]["resource"], "documents")
        self.assertIsNone(manifest.results[0].output_path)

    async def test_collect_drawing_and_specification_helpers(self) -> None:
        """Drawing and specification collection helpers should avoid file output."""
        drawings = await async_collect_multi_project_drawings(
            FakeAsyncClient(),  # type: ignore[arg-type]
            company_id=12345,
            project_ids=[67890],
        )
        specs = await async_collect_multi_project_specifications(
            FakeAsyncClient(),  # type: ignore[arg-type]
            company_id=12345,
            project_ids=[67890],
        )

        self.assertEqual(drawings.results[0].records[0]["resource"], "drawings")
        self.assertEqual(specs.results[0].records[0]["resource"], "specification_sections")

    async def test_partial_failures_are_redacted_when_continuing(self) -> None:
        """Partial failures should be captured without leaking token-like values or signed URLs."""
        manifest = await async_collect_multi_project_rfis(
            FakeAsyncClient(fail_project=11111),  # type: ignore[arg-type]
            company_id=12345,
            project_ids=[67890, 11111],
            continue_on_error=True,
        )

        self.assertEqual(manifest.completed_count, 1)
        self.assertEqual(manifest.failed_count, 1)
        serialized = manifest.model_dump_json()
        self.assertNotIn("=secret", serialized)
        self.assertNotIn("token=secret", serialized)
        self.assertNotIn("signed.example.com", serialized)

    async def test_fail_fast_raises(self) -> None:
        """continue_on_error=False should stop on the first failure."""
        with self.assertRaises(RuntimeError):
            await async_collect_multi_project_submittals(
                FakeAsyncClient(fail_project=11111),  # type: ignore[arg-type]
                company_id=12345,
                project_ids=[11111, 67890],
                continue_on_error=False,
            )

    async def test_concurrency_limit_is_respected(self) -> None:
        """Batch runner should not exceed max_concurrency."""
        client = FakeAsyncClient(delay=0.01)
        await async_collect_multi_project_rfis(
            client,  # type: ignore[arg-type]
            company_id=12345,
            project_ids=[1, 2, 3, 4, 5],
            max_concurrency=2,
        )

        self.assertLessEqual(client.max_active, 2)

    async def test_resume_manifest_skips_completed_pairs(self) -> None:
        """Completed project/resource pairs from a manifest should be skipped."""
        with tempfile.TemporaryDirectory() as temp_dir:
            plan = build_async_batch_plan(
                company_id=12345,
                project_ids=[67890],
                resources=["rfis", "submittals"],
                output_dir=temp_dir,
                dry_run=False,
            )
            previous = build_async_batch_dry_run_manifest(plan)
            previous.results[0] = AsyncBatchResourceResult(
                project_id=67890,
                resource="rfis",
                status="completed",
                record_count=1,
            )

            manifest = await async_run_project_batch(
                FakeAsyncClient(),  # type: ignore[arg-type]
                plan,
                resume_manifest=previous,
            )

            statuses = {(result.resource, result.status) for result in manifest.results}
            self.assertIn(("rfis", "skipped"), statuses)
            self.assertIn(("submittals", "completed"), statuses)

    async def test_resume_manifest_path_skips_completed_pairs(self) -> None:
        """A previous manifest path should support the resume skip pattern."""
        with tempfile.TemporaryDirectory() as temp_dir:
            plan = build_async_batch_plan(
                company_id=12345,
                project_ids=[67890],
                resources=["rfis"],
                output_dir=temp_dir,
                dry_run=False,
            )
            previous = build_async_batch_dry_run_manifest(plan)
            previous.results[0].status = "completed"
            previous_path = write_async_batch_manifest(previous, Path(temp_dir) / "previous.json")

            manifest = await async_run_project_batch(
                FakeAsyncClient(),  # type: ignore[arg-type]
                plan,
                resume_manifest=previous_path,
            )

            self.assertEqual(manifest.skipped_count, 1)
            self.assertEqual(manifest.projects[0].status, "skipped")

    async def test_dry_run_batch_does_not_call_client(self) -> None:
        """Dry-run execution should avoid Procore calls."""
        client = FakeAsyncClient()
        plan = build_async_batch_plan(
            company_id=12345,
            project_ids=[67890],
            resources=["rfis"],
            dry_run=True,
        )

        manifest = await async_export_multi_project_resources(
            client,  # type: ignore[arg-type]
            plan,
        )

        self.assertTrue(manifest.dry_run)
        self.assertEqual(client.calls, [])

    async def test_invalid_runtime_plan_raises_validation_error(self) -> None:
        """Runtime should refuse invalid plans before any client call."""
        plan = build_async_batch_plan(
            company_id=12345,
            project_ids=[67890],
            resources=["unknown"],
            dry_run=False,
        )

        with self.assertRaises(ValidationError):
            await async_run_project_batch(FakeAsyncClient(), plan)  # type: ignore[arg-type]

    async def test_unknown_resource_fetch_guard_raises_validation_error(self) -> None:
        """Private resource fetch guard should reject unsupported resources."""
        with self.assertRaises(ValidationError):
            await async_batch_module._fetch_resource(  # pylint: disable=protected-access
                FakeAsyncClient(),  # type: ignore[arg-type]
                12345,
                67890,
                "unknown",
                {},
            )


class Phase10CAsyncBatchCliTests(unittest.TestCase):
    """Validate local-only CLI support."""

    def test_cli_sample_config_outputs_json(self) -> None:
        """The CLI sample-config command should not require credentials."""
        result = run_command(
            Namespace(command="async-batch", async_batch_command="sample-config", output=None)
        )
        payload = json.loads(result)

        self.assertEqual(payload["company_id"], 12345)
        self.assertTrue(payload["dry_run"])

    def test_cli_validate_returns_manifest(self) -> None:
        """The CLI validate command should return a local manifest."""
        result = run_command(
            Namespace(
                command="async-batch",
                async_batch_command="validate",
                plan_path=PROJECT_ROOT / "examples" / "configs" / "async_batch_dry_run.json",
            )
        )

        self.assertIsInstance(result, AsyncBatchManifest)
        self.assertTrue(result.dry_run)

    def test_cli_dry_run_main_prints_no_live_call_message(self) -> None:
        """The CLI dry-run command should print a local-only message."""
        plan_path = PROJECT_ROOT / "examples" / "configs" / "async_batch_dry_run.json"
        stdout = StringIO()
        with redirect_stdout(stdout):
            with patch(
                "sys.argv",
                ["procore-sdk", "async-batch", "dry-run", str(plan_path)],
            ):
                main()

        self.assertIn("no Procore API calls", stdout.getvalue())

    def test_cli_dry_run_can_write_manifest(self) -> None:
        """The CLI dry-run command can write a local manifest JSON."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "manifest.json"
            result = run_command(
                Namespace(
                    command="async-batch",
                    async_batch_command="dry-run",
                    plan_path=PROJECT_ROOT / "examples" / "configs" / "async_batch_dry_run.json",
                    write_manifest=output_path,
                    json_output=False,
                )
            )

            self.assertEqual(result, output_path)
            self.assertTrue(output_path.exists())


class Phase10CAsyncBatchSafetyTests(unittest.TestCase):
    """Validate safety boundaries remain in place."""

    def test_examples_readme_documents_153_to_160(self) -> None:
        """Examples README should mention Phase 10C examples."""
        readme = (PROJECT_ROOT / "examples" / "README.md").read_text(encoding="utf-8")

        self.assertIn("153_async_batch_plan.py", readme)
        self.assertIn("160_phase10c_async_batch_summary.py", readme)

    def test_package_root_exports_phase10c_helpers(self) -> None:
        """Phase 10C helpers should be exported from package root."""
        self.assertTrue(hasattr(pyprocore, "AsyncBatchPlan"))
        self.assertTrue(hasattr(pyprocore, "async_export_multi_project_rfis"))

    def test_no_procore_write_action_helpers_added(self) -> None:
        """Async batch module should not expose Procore mutation helpers."""
        forbidden_prefixes = ("create_", "update_", "delete_", "upload_", "approve_")
        exported = getattr(async_batch_module, "__all__")
        self.assertFalse(
            [
                name
                for name in exported
                if name.startswith(forbidden_prefixes) and name != "write_async_batch_manifest"
            ]
        )

    def test_agent_and_mcp_execution_remain_disabled(self) -> None:
        """Agent/MCP execution-disabled response should remain unchanged."""
        response = pyprocore.build_mcp_tool_execution_disabled_response("list_rfis")
        self.assertFalse(response["isError"] is False)
        self.assertIn("disabled", json.dumps(response).lower())


if __name__ == "__main__":
    unittest.main()
