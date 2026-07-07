"""Unit tests for workflow export and sync helpers."""

from __future__ import annotations

import csv
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock, patch

from pyprocore.models import RFI, RFIQuestion, Status, Submittal
from pyprocore.workflows import (
    ProjectSyncResult,
    SyncResult,
    export_rfis_to_csv,
    export_rfis_to_jsonl,
    export_submittals_to_csv,
    export_submittals_to_jsonl,
    sync_project_to_folder,
    sync_rfis_to_folder,
    sync_submittals_to_folder,
)
from pyprocore.workflows.state import build_sync_state_path, load_sync_state
from pyprocore.workflows.utils import (
    attachment_count,
    get_value,
    item_title,
    model_to_dict,
    safe_filename,
    scalar_text,
)


class WorkflowExportTestCase(unittest.TestCase):
    """Validate CSV and JSONL export helpers."""

    @patch("pyprocore.workflows.exports.list_rfis")
    def test_export_rfis_to_csv_writes_rows_and_passes_filters(self, list_rfis: Mock) -> None:
        """RFI CSV exports write typed model values and pass query filters."""
        list_rfis.return_value = [
            RFI(
                id=10,
                number="15",
                subject="Door hardware",
                status=Status(name="Open"),
                questions=[
                    RFIQuestion(
                        plain_text_body="Which hardware?",
                        attachments=[{"url": "https://signed.example/one.pdf"}],
                    )
                ],
                created_at="2026-07-01",
                updated_at="2026-07-02",
                due_date="2026-07-10",
                ball_in_court={"name": "Architect"},
                responsible_contractor={"name": "ACME"},
            )
        ]

        with TemporaryDirectory() as temporary_directory:
            output = Path(temporary_directory) / "exports" / "rfis.csv"
            result = export_rfis_to_csv(
                352338,
                output,
                status="open",
                updated_after="2026-07-01",
                params={"per_page": 100},
                sort="number",
            )

            with result.open(encoding="utf-8") as file_handle:
                rows = list(csv.DictReader(file_handle))

        self.assertEqual(result, output)
        self.assertEqual(rows[0]["id"], "10")
        self.assertEqual(rows[0]["number"], "15")
        self.assertEqual(rows[0]["subject"], "Door hardware")
        self.assertEqual(rows[0]["status"], "Open")
        self.assertEqual(rows[0]["attachment_count"], "1")
        list_rfis.assert_called_once_with(
            352338,
            status="open",
            updated_after="2026-07-01",
            updated_before=None,
            created_after=None,
            created_before=None,
            params={"per_page": 100},
            sort="number",
        )

    @patch("pyprocore.workflows.exports.list_submittals")
    def test_export_submittals_to_csv_writes_rows(self, list_submittals: Mock) -> None:
        """Submittal CSV exports write typed model values."""
        list_submittals.return_value = [
            Submittal(
                id=20,
                number="27",
                title="Concrete mix",
                status="pending",
                responsible_contractor={"name": "Concrete Co"},
                attachments=[{"url": "https://signed.example/spec.pdf"}],
            )
        ]

        with TemporaryDirectory() as temporary_directory:
            output = Path(temporary_directory) / "submittals.csv"
            result = export_submittals_to_csv(352338, output, status="pending")

            with result.open(encoding="utf-8") as file_handle:
                rows = list(csv.DictReader(file_handle))

        self.assertEqual(rows[0]["title"], "Concrete mix")
        self.assertEqual(rows[0]["responsible_contractor"], "Concrete Co")
        self.assertEqual(rows[0]["attachment_count"], "1")
        list_submittals.assert_called_once()

    @patch("pyprocore.workflows.exports.list_rfis")
    def test_export_rfis_to_jsonl_writes_one_model_per_line(self, list_rfis: Mock) -> None:
        """RFI JSONL exports use JSON-serializable typed model payloads."""
        list_rfis.return_value = [RFI(id=10, number="15", subject="Door hardware")]

        with TemporaryDirectory() as temporary_directory:
            output = export_rfis_to_jsonl(352338, Path(temporary_directory) / "rfis.jsonl")
            lines = output.read_text(encoding="utf-8").splitlines()

        self.assertEqual(len(lines), 1)
        self.assertEqual(json.loads(lines[0])["subject"], "Door hardware")

    @patch("pyprocore.workflows.exports.list_submittals")
    def test_export_submittals_to_jsonl_writes_one_model_per_line(
        self,
        list_submittals: Mock,
    ) -> None:
        """Submittal JSONL exports use JSON-serializable typed model payloads."""
        list_submittals.return_value = [Submittal(id=20, number="27", title="Concrete mix")]

        with TemporaryDirectory() as temporary_directory:
            output = export_submittals_to_jsonl(
                352338,
                Path(temporary_directory) / "submittals.jsonl",
            )
            lines = output.read_text(encoding="utf-8").splitlines()

        self.assertEqual(len(lines), 1)
        self.assertEqual(json.loads(lines[0])["title"], "Concrete mix")

    @patch("pyprocore.workflows.exports.list_rfis")
    def test_export_rfis_to_csv_handles_missing_fields(self, list_rfis: Mock) -> None:
        """CSV exports keep a stable shape when optional fields are missing."""
        list_rfis.return_value = [RFI(id=10)]

        with TemporaryDirectory() as temporary_directory:
            output = export_rfis_to_csv(352338, Path(temporary_directory) / "rfis.csv")
            with output.open(encoding="utf-8") as file_handle:
                rows = list(csv.DictReader(file_handle))

        self.assertEqual(rows[0]["id"], "10")
        self.assertEqual(rows[0]["subject"], "")
        self.assertEqual(rows[0]["attachment_count"], "0")


class WorkflowSyncTestCase(unittest.TestCase):
    """Validate folder sync workflow helpers."""

    def test_safe_filename_removes_unsafe_characters(self) -> None:
        """Unsafe path characters are removed from generated folder names."""
        self.assertEqual(safe_filename("RFI: 15 / Door? <Issue>"), "RFI_ 15 _ Door_ _Issue_")
        self.assertEqual(safe_filename("   "), "item")
        self.assertEqual(safe_filename("../secret"), "_secret")
        self.assertEqual(safe_filename("..."), "item")
        self.assertEqual(safe_filename("a" * 200, max_length=40), "a" * 40)
        self.assertEqual(safe_filename("RFI 15", fallback="one"), safe_filename("RFI 15"))

    def test_workflow_utils_handle_common_payload_shapes(self) -> None:
        """Utility helpers support mappings, models, lists, and missing values."""
        rfi = RFI(
            id=10,
            number="15",
            subject="Door hardware",
            questions=[
                {
                    "attachments": [
                        {"url": "https://signed.example/one.pdf"},
                        {"url": "https://signed.example/two.pdf"},
                    ]
                }
            ],
        )

        self.assertEqual(model_to_dict(rfi)["id"], 10)
        self.assertEqual(model_to_dict({"id": 1}), {"id": 1})
        self.assertEqual(model_to_dict("text"), {"value": "text"})
        self.assertEqual(get_value({"name": "Architect"}, "name"), "Architect")
        self.assertIsNone(get_value(object(), "missing"))
        self.assertEqual(scalar_text({"name": "Architect"}), "Architect")
        self.assertEqual(scalar_text([{"name": "A"}, {"name": "B"}]), "A; B")
        self.assertEqual(item_title({"title": "Concrete"}, fallback="Fallback"), "Concrete")
        self.assertEqual(item_title({}, fallback="Fallback"), "Fallback")
        self.assertEqual(attachment_count(rfi, item_type="rfi"), 2)
        self.assertEqual(attachment_count({"questions": "bad"}, item_type="rfi"), 0)
        self.assertEqual(attachment_count({"attachments": "bad"}, item_type="submittal"), 0)

    @patch("pyprocore.workflows.sync.download_rfi_attachments")
    @patch("pyprocore.workflows.sync.list_rfis")
    def test_sync_rfis_to_folder_writes_artifacts(
        self,
        list_rfis: Mock,
        download_rfi_attachments: Mock,
    ) -> None:
        """RFI sync writes item JSON, Markdown, tracker, manifest, and downloads."""
        list_rfis.return_value = [
            RFI(
                id=10,
                number="15",
                subject="Door hardware",
                questions=[RFIQuestion(plain_text_body="Which hardware?")],
            )
        ]
        download_rfi_attachments.return_value = [Path("door.pdf")]

        with TemporaryDirectory() as temporary_directory:
            result = sync_rfis_to_folder(
                352338,
                temporary_directory,
                status="open",
                updated_after="2026-07-01",
                overwrite=True,
            )
            root = Path(temporary_directory)
            item_folder = root / "rfis" / "RFI-15 - Door hardware"

            self.assertIsInstance(result, SyncResult)
            self.assertEqual(result.item_count, 1)
            self.assertTrue((item_folder / "item.json").exists())
            self.assertTrue((item_folder / "summary.md").exists())
            self.assertTrue((root / "rfi_tracker.csv").exists())
            self.assertTrue((root / "sync_manifest.json").exists())
            manifest = json.loads((root / "sync_manifest.json").read_text(encoding="utf-8"))

        self.assertEqual(manifest["item_count"], 1)
        self.assertEqual(manifest["item_type"], "rfi")
        self.assertEqual(manifest["project_id"], 352338)
        self.assertIn("created_at", manifest)
        self.assertEqual(manifest["items"][0]["status"], None)
        self.assertEqual(manifest["items"][0]["summary_path"], str(item_folder / "summary.md"))
        self.assertEqual(manifest["items"][0]["item_json_path"], str(item_folder / "item.json"))
        self.assertEqual(manifest["items"][0]["attachment_count"], 0)
        self.assertEqual(result.manifest_path, root / "sync_manifest.json")
        self.assertEqual(result.downloaded_files, [Path("door.pdf")])
        list_rfis.assert_called_once_with(
            352338,
            status="open",
            updated_after="2026-07-01",
        )
        download_rfi_attachments.assert_called_once()
        self.assertTrue(download_rfi_attachments.call_args.kwargs["overwrite"])

    @patch("pyprocore.workflows.sync.download_submittal_attachments")
    @patch("pyprocore.workflows.sync.list_submittals")
    def test_sync_submittals_to_folder_can_skip_optional_artifacts(
        self,
        list_submittals: Mock,
        download_submittal_attachments: Mock,
    ) -> None:
        """Submittal sync supports disabling attachments, tracker, and Markdown."""
        list_submittals.return_value = [
            Submittal(id=20, number="27", title="Concrete mix", attachments=[])
        ]

        with TemporaryDirectory() as temporary_directory:
            result = sync_submittals_to_folder(
                352338,
                temporary_directory,
                download_attachments=False,
                create_tracker=False,
                create_markdown=False,
            )
            root = Path(temporary_directory)
            item_folder = root / "submittals" / "SUB-27 - Concrete mix"

            self.assertEqual(result.item_type, "submittal")
            self.assertIsNone(result.tracker_path)
            self.assertFalse(result.dry_run)
            self.assertIn("Attachment downloads were disabled.", result.warnings)
            self.assertTrue((item_folder / "item.json").exists())
            self.assertFalse((item_folder / "summary.md").exists())
            self.assertFalse((root / "submittal_tracker.csv").exists())
            self.assertTrue((root / "sync_manifest.json").exists())

        download_submittal_attachments.assert_not_called()

    @patch("pyprocore.workflows.sync.download_rfi_attachments")
    @patch("pyprocore.workflows.sync.list_rfis")
    def test_sync_rfis_to_folder_dry_run_does_not_write_files(
        self,
        list_rfis: Mock,
        download_rfi_attachments: Mock,
    ) -> None:
        """Dry-run sync plans outputs without creating folders or files."""
        list_rfis.return_value = [RFI(id=10, number="15", subject="Door hardware")]

        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory) / "planned"
            result = sync_rfis_to_folder(352338, root, dry_run=True)

            self.assertTrue(result.dry_run)
            self.assertIsNone(result.manifest_path)
            self.assertEqual(result.tracker_path, root / "rfi_tracker.csv")
            self.assertEqual(
                result.items[0].item_json_path,
                root / "rfis" / "RFI-15 - Door hardware" / "item.json",
            )
            self.assertFalse(root.exists())

        download_rfi_attachments.assert_not_called()

    @patch("pyprocore.workflows.sync.download_submittal_attachments")
    @patch("pyprocore.workflows.sync.list_submittals")
    def test_sync_submittals_to_folder_writes_markdown_and_downloads(
        self,
        list_submittals: Mock,
        download_submittal_attachments: Mock,
    ) -> None:
        """Submittal sync writes summaries and downloads when enabled."""
        list_submittals.return_value = [
            Submittal(
                id=20,
                number="27",
                title="Concrete mix",
                description="Mix design details",
                responsible_contractor={"name": "Concrete Co"},
            )
        ]
        download_submittal_attachments.return_value = [Path("mix.pdf")]

        with TemporaryDirectory() as temporary_directory:
            result = sync_submittals_to_folder(
                352338,
                temporary_directory,
                status="pending",
                overwrite=True,
            )
            root = Path(temporary_directory)
            item_folder = root / "submittals" / "SUB-27 - Concrete mix"
            summary = (item_folder / "summary.md").read_text(encoding="utf-8")

            self.assertEqual(result.item_count, 1)
            self.assertIn("Mix design details", summary)
            self.assertTrue((root / "submittal_tracker.csv").exists())

        list_submittals.assert_called_once_with(352338, status="pending")
        download_submittal_attachments.assert_called_once()
        self.assertTrue(download_submittal_attachments.call_args.kwargs["overwrite"])

    @patch("pyprocore.workflows.sync.download_rfi_attachments")
    @patch("pyprocore.workflows.sync.list_rfis")
    def test_incremental_sync_writes_state_and_skips_unchanged_items(
        self,
        list_rfis: Mock,
        download_rfi_attachments: Mock,
    ) -> None:
        """Incremental RFI sync writes state and skips unchanged items later."""
        first = [RFI(id=10, number="15", subject="Door hardware", updated_at="2026-07-01")]
        second = [RFI(id=10, number="15", subject="Door hardware", updated_at="2026-07-01")]
        list_rfis.side_effect = [first, second]

        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            first_result = sync_rfis_to_folder(352338, root, incremental=True)
            state_path = build_sync_state_path(root, "rfi")
            state = load_sync_state(state_path)
            second_result = sync_rfis_to_folder(352338, root, incremental=True)

            manifest = json.loads((root / "sync_manifest.json").read_text(encoding="utf-8"))

        self.assertEqual(first_result.synced_count, 1)
        self.assertEqual(first_result.state_path, state_path)
        self.assertEqual(state.items["10"].updated_at, "2026-07-01")
        self.assertEqual(second_result.synced_count, 0)
        self.assertEqual(second_result.skipped_count, 1)
        self.assertEqual(manifest["skipped_count"], 1)
        self.assertEqual(manifest["skipped_items"][0]["id"], 10)
        self.assertEqual(download_rfi_attachments.call_count, 1)

    @patch("pyprocore.workflows.sync.download_rfi_attachments")
    @patch("pyprocore.workflows.sync.list_rfis")
    def test_incremental_sync_resyncs_changed_and_new_items(
        self,
        list_rfis: Mock,
        download_rfi_attachments: Mock,
    ) -> None:
        """Incremental sync writes changed and new items."""
        list_rfis.side_effect = [
            [RFI(id=10, number="15", updated_at="2026-07-01")],
            [
                RFI(id=10, number="15", updated_at="2026-07-02"),
                RFI(id=11, number="16", updated_at="2026-07-02"),
            ],
        ]

        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            sync_rfis_to_folder(352338, root, incremental=True)
            result = sync_rfis_to_folder(352338, root, incremental=True)

        self.assertEqual(result.synced_count, 2)
        self.assertEqual(result.skipped_count, 0)
        self.assertEqual(download_rfi_attachments.call_count, 3)

    @patch("pyprocore.workflows.sync.download_rfi_attachments")
    @patch("pyprocore.workflows.sync.list_rfis")
    def test_incremental_dry_run_does_not_write_state(
        self,
        list_rfis: Mock,
        download_rfi_attachments: Mock,
    ) -> None:
        """Incremental dry-run does not write state or attachments."""
        list_rfis.return_value = [RFI(id=10, number="15", updated_at="2026-07-01")]

        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory) / "dry"
            result = sync_rfis_to_folder(352338, root, incremental=True, dry_run=True)

            self.assertFalse(build_sync_state_path(root, "rfi").exists())
            self.assertFalse(root.exists())

        self.assertTrue(result.incremental)
        self.assertEqual(result.synced_count, 1)
        download_rfi_attachments.assert_not_called()

    @patch("pyprocore.workflows.sync.download_rfi_attachments")
    @patch("pyprocore.workflows.sync.list_rfis")
    def test_corrupted_incremental_state_warns_and_full_syncs(
        self,
        list_rfis: Mock,
        download_rfi_attachments: Mock,
    ) -> None:
        """Unreadable state falls back to a full sync with a warning."""
        list_rfis.return_value = [RFI(id=10, number="15", updated_at="2026-07-01")]

        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            state_path = build_sync_state_path(root, "rfi")
            state_path.write_text("{bad json", encoding="utf-8")
            result = sync_rfis_to_folder(352338, root, incremental=True)

        self.assertEqual(result.synced_count, 1)
        self.assertTrue(any("Could not read sync state" in warning for warning in result.warnings))
        download_rfi_attachments.assert_called_once()

    @patch("pyprocore.workflows.sync.sync_submittals_to_folder")
    @patch("pyprocore.workflows.sync.sync_rfis_to_folder")
    def test_sync_project_to_folder_combines_child_results(
        self,
        sync_rfis: Mock,
        sync_submittals: Mock,
    ) -> None:
        """Project sync calls child syncs and writes project reports."""
        sync_rfis.return_value = SyncResult(
            output_dir=Path("out"),
            item_type="rfi",
            project_id=352338,
            item_count=2,
            synced_count=2,
            skipped_count=0,
        )
        sync_submittals.return_value = SyncResult(
            output_dir=Path("out"),
            item_type="submittal",
            project_id=352338,
            item_count=1,
            synced_count=0,
            skipped_count=1,
            warnings=["Attachment downloads were disabled."],
        )

        with TemporaryDirectory() as temporary_directory:
            result = sync_project_to_folder(
                352338,
                temporary_directory,
                download_attachments=False,
                incremental=True,
            )
            root = Path(temporary_directory)
            manifest = json.loads((root / "project_sync_manifest.json").read_text(encoding="utf-8"))

        self.assertIsInstance(result, ProjectSyncResult)
        self.assertEqual(result.item_count, 3)
        self.assertEqual(result.synced_count, 2)
        self.assertEqual(result.skipped_count, 1)
        self.assertTrue(result.incremental)
        self.assertTrue(
            result.summary_path and result.summary_path.name == "project_sync_summary.md"
        )
        self.assertEqual(manifest["project_id"], 352338)
        sync_rfis.assert_called_once()
        sync_submittals.assert_called_once()

    @patch("pyprocore.workflows.sync.sync_submittals_to_folder")
    @patch("pyprocore.workflows.sync.sync_rfis_to_folder")
    def test_sync_project_to_folder_supports_inclusion_flags_and_dry_run(
        self,
        sync_rfis: Mock,
        sync_submittals: Mock,
    ) -> None:
        """Project sync can run one child type and avoid project reports in dry-run."""
        sync_rfis.return_value = SyncResult(
            output_dir=Path("out"),
            item_type="rfi",
            project_id=352338,
            item_count=1,
            synced_count=1,
            dry_run=True,
        )

        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory) / "project"
            result = sync_project_to_folder(
                352338,
                root,
                include_submittals=False,
                dry_run=True,
                status="open",
            )

        self.assertTrue(result.dry_run)
        self.assertIsNone(result.manifest_path)
        self.assertFalse(root.exists())
        sync_rfis.assert_called_once()
        sync_submittals.assert_not_called()


if __name__ == "__main__":
    unittest.main()
    sync_project_to_folder,
