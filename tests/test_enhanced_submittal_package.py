"""Unit tests for enhanced submittal package workflows."""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock, patch

from pyprocore.core.exceptions import ValidationError
from pyprocore.models import RFI, Submittal
from pyprocore.workflows import (
    EnhancedSubmittalPackageResult,
    build_enhanced_submittal_package,
)


class EnhancedSubmittalPackageTestCase(unittest.TestCase):
    """Validate enhanced AI-ready submittal package creation."""

    @patch("pyprocore.workflows.enhanced_submittal.get_submittal")
    def test_submittal_lookup_by_id_writes_core_and_ai_files(
        self,
        get_submittal: Mock,
    ) -> None:
        """Submittal ID lookup writes primary package artifacts."""
        get_submittal.return_value = Submittal(
            id=20,
            number="27",
            title="Door hardware",
            description="Submit door hardware data.",
        )

        with TemporaryDirectory() as temporary_directory:
            result = build_enhanced_submittal_package(
                352338,
                submittal_id=20,
                output_dir=temporary_directory,
                include_related=False,
            )
            root = Path(temporary_directory)

            self.assertIsInstance(result, EnhancedSubmittalPackageResult)
            self.assertTrue((root / "manifest.json").exists())
            self.assertTrue((root / "summary.md").exists())
            self.assertTrue((root / "submittal.json").exists())
            self.assertTrue((root / "submittal.md").exists())
            self.assertTrue((root / "ai" / "review_context.md").exists())
            self.assertTrue((root / "ai" / "review_context.json").exists())
            self.assertTrue((root / "ai" / "questions_to_answer.md").exists())
            self.assertTrue((root / "ai" / "risk_flags.md").exists())
            self.assertTrue((root / "ai" / "approval_review.md").exists())

        get_submittal.assert_called_once_with(352338, 20)

    @patch("pyprocore.workflows.enhanced_submittal.find_submittal")
    def test_submittal_lookup_by_number(self, find_submittal: Mock) -> None:
        """Submittal number lookup uses the resolver."""
        find_submittal.return_value = Submittal(id=20, number="27", title="Door hardware")

        with TemporaryDirectory() as temporary_directory:
            result = build_enhanced_submittal_package(
                352338,
                submittal_number="27",
                output_dir=temporary_directory,
                include_related=False,
            )

        self.assertEqual(result.submittal_number, "27")
        find_submittal.assert_called_once_with(352338, number="27")

    def test_invalid_inputs_raise_validation_error(self) -> None:
        """Missing submittal identifiers and unknown related sections fail clearly."""
        with TemporaryDirectory() as temporary_directory:
            with self.assertRaisesRegex(ValidationError, "Provide submittal_id"):
                build_enhanced_submittal_package(352338, output_dir=temporary_directory)
            with self.assertRaisesRegex(ValidationError, "Unknown related section"):
                build_enhanced_submittal_package(
                    352338,
                    submittal_id=20,
                    output_dir=temporary_directory,
                    related_sections=["weather"],
                )

    @patch("pyprocore.workflows.enhanced_submittal.list_rfis")
    @patch("pyprocore.workflows.enhanced_submittal.get_submittal")
    def test_keyword_matching_and_max_related_items(
        self,
        get_submittal: Mock,
        list_rfis: Mock,
    ) -> None:
        """Related items are matched with simple keyword scoring and limited."""
        get_submittal.return_value = Submittal(id=20, number="27", title="Door hardware")
        list_rfis.return_value = [
            RFI(id=1, number="1", subject="Door hardware coordination"),
            RFI(id=2, number="2", subject="Unrelated concrete mix"),
        ]

        with TemporaryDirectory() as temporary_directory:
            build_enhanced_submittal_package(
                352338,
                submittal_id=20,
                output_dir=temporary_directory,
                related_sections=["rfis"],
                max_related_items=1,
            )
            related = json.loads(
                (Path(temporary_directory) / "related" / "rfis.json").read_text(encoding="utf-8")
            )

        self.assertEqual(len(related), 1)
        self.assertEqual(related[0]["subject"], "Door hardware coordination")

    @patch("pyprocore.workflows.enhanced_submittal.list_rfis")
    @patch("pyprocore.workflows.enhanced_submittal.list_documents")
    @patch("pyprocore.workflows.enhanced_submittal.get_submittal")
    def test_related_include_and_exclude(
        self,
        get_submittal: Mock,
        list_documents: Mock,
        list_rfis: Mock,
    ) -> None:
        """include/exclude controls related section attempts."""
        get_submittal.return_value = Submittal(id=20, number="27", title="Door hardware")
        list_documents.return_value = [{"id": 1, "name": "Door hardware plan"}]
        list_rfis.return_value = [RFI(id=2, subject="Door hardware")]

        with TemporaryDirectory() as temporary_directory:
            result = build_enhanced_submittal_package(
                352338,
                submittal_id=20,
                output_dir=temporary_directory,
                related_sections=["documents", "rfis"],
                exclude_related=["rfis"],
            )

        self.assertEqual(result.manifest.sections_attempted, ["documents"])
        list_documents.assert_called_once()
        list_rfis.assert_not_called()

    @patch("pyprocore.workflows.enhanced_submittal.list_daily_logs_for_date")
    @patch("pyprocore.workflows.enhanced_submittal.list_daily_log_headers")
    @patch("pyprocore.workflows.enhanced_submittal.get_daily_log_counts")
    @patch("pyprocore.workflows.enhanced_submittal.list_photos")
    @patch("pyprocore.workflows.enhanced_submittal.list_photo_albums")
    @patch("pyprocore.workflows.enhanced_submittal.list_specification_sections")
    @patch("pyprocore.workflows.enhanced_submittal.list_drawings")
    @patch("pyprocore.workflows.enhanced_submittal.list_drawing_areas")
    @patch("pyprocore.workflows.enhanced_submittal.list_documents")
    @patch("pyprocore.workflows.enhanced_submittal.list_rfis")
    @patch("pyprocore.workflows.enhanced_submittal.get_submittal")
    def test_related_project_context_sections_are_written(
        self,
        get_submittal: Mock,
        list_rfis: Mock,
        list_documents: Mock,
        list_drawing_areas: Mock,
        list_drawings: Mock,
        list_specification_sections: Mock,
        list_photo_albums: Mock,
        list_photos: Mock,
        get_daily_log_counts: Mock,
        list_daily_log_headers: Mock,
        list_daily_logs_for_date: Mock,
    ) -> None:
        """Related project tools are fetched, matched, and written safely."""
        get_submittal.return_value = Submittal(
            id=20,
            number="27",
            title="Door hardware",
            status="open",
            due_date="2020-01-01",
            description="Door hardware review.",
        )
        list_rfis.return_value = [RFI(id=1, subject="Door hardware RFI")]
        list_documents.return_value = [{"id": 2, "name": "Door hardware.pdf"}]
        list_drawing_areas.return_value = [{"id": 7, "name": "Architectural"}]
        list_drawings.return_value = [{"id": 8, "number": "A-101", "title": "Door hardware"}]
        list_specification_sections.return_value = [
            {"id": 9, "number": "08 7100", "title": "Door Hardware"}
        ]
        list_photo_albums.return_value = [{"id": 11, "name": "Punch"}]
        list_photos.return_value = [{"id": 12, "filename": "door-hardware.jpg"}]
        get_daily_log_counts.return_value = [
            {"log_type": "notes", "name": "Door hardware", "count": 1}
        ]
        list_daily_log_headers.return_value = [{"id": 13, "log_date": "2020-01-01"}]
        list_daily_logs_for_date.return_value = Mock(
            logs={"notes": [{"id": 14, "comments": "Door hardware discussion"}]}
        )

        with TemporaryDirectory() as temporary_directory:
            result = build_enhanced_submittal_package(
                352338,
                submittal_id=20,
                company_id=123,
                output_dir=temporary_directory,
                related_sections=[
                    "rfis",
                    "documents",
                    "drawings",
                    "specifications",
                    "photos",
                    "daily_logs",
                ],
                log_date="2020-01-01",
            )
            root = Path(temporary_directory)
            risk_flags = (root / "ai" / "risk_flags.md").read_text(encoding="utf-8")

            self.assertTrue((root / "related" / "rfis.json").exists())
            self.assertTrue((root / "related" / "documents.md").exists())
            self.assertTrue((root / "related" / "drawings.json").exists())
            self.assertTrue((root / "related" / "specifications.json").exists())
            self.assertTrue((root / "related" / "photos.json").exists())
            self.assertTrue((root / "related" / "daily_logs.json").exists())
            self.assertEqual(result.manifest.sections_failed, [])
            self.assertEqual(result.manifest.related_item_counts["rfis"], 1)
            self.assertIn("Possible overdue submittal", risk_flags)
            self.assertIn("Related RFIs were found", risk_flags)

        list_drawings.assert_called_once_with(
            352338,
            company_id=123,
            drawing_area_id=7,
        )
        list_photos.assert_called_once_with(352338, company_id=123, album_id=11)
        list_daily_logs_for_date.assert_called_once_with(
            352338,
            company_id=123,
            log_date="2020-01-01",
        )

    @patch("pyprocore.workflows.enhanced_submittal.download_submittal_attachments")
    @patch("pyprocore.workflows.enhanced_submittal.get_submittal")
    def test_download_files_false_does_not_download(
        self,
        get_submittal: Mock,
        download_submittal_attachments: Mock,
    ) -> None:
        """Submittal attachment downloads are off by default."""
        get_submittal.return_value = Submittal(id=20, number="27")

        with TemporaryDirectory() as temporary_directory:
            build_enhanced_submittal_package(
                352338,
                submittal_id=20,
                output_dir=temporary_directory,
                include_related=False,
            )

        download_submittal_attachments.assert_not_called()

    @patch("pyprocore.workflows.enhanced_submittal.download_submittal_attachments")
    @patch("pyprocore.workflows.enhanced_submittal.get_submittal")
    def test_download_files_true_downloads(
        self,
        get_submittal: Mock,
        download_submittal_attachments: Mock,
    ) -> None:
        """Submittal attachment downloads run only when requested."""
        get_submittal.return_value = Submittal(id=20, number="27")
        download_submittal_attachments.return_value = [Path("one.pdf")]

        with TemporaryDirectory() as temporary_directory:
            result = build_enhanced_submittal_package(
                352338,
                submittal_id=20,
                output_dir=temporary_directory,
                include_related=False,
                download_files=True,
                overwrite=True,
            )

        self.assertTrue(result.manifest.downloads_enabled)
        download_submittal_attachments.assert_called_once()
        self.assertTrue(download_submittal_attachments.call_args.kwargs["overwrite"])

    @patch("pyprocore.workflows.enhanced_submittal.list_rfis")
    @patch("pyprocore.workflows.enhanced_submittal.get_submittal")
    def test_continue_on_error_records_related_error(
        self,
        get_submittal: Mock,
        list_rfis: Mock,
    ) -> None:
        """Related section errors are recorded when continue_on_error is true."""
        get_submittal.return_value = Submittal(id=20, number="27", title="Door hardware")
        list_rfis.side_effect = RuntimeError("no rfi access")

        with TemporaryDirectory() as temporary_directory:
            result = build_enhanced_submittal_package(
                352338,
                submittal_id=20,
                output_dir=temporary_directory,
                related_sections=["rfis"],
            )

        self.assertEqual(result.manifest.sections_failed, ["rfis"])
        self.assertTrue(result.errors_path)

    @patch("pyprocore.workflows.enhanced_submittal.list_rfis")
    @patch("pyprocore.workflows.enhanced_submittal.get_submittal")
    def test_fail_fast_raises_related_error(
        self,
        get_submittal: Mock,
        list_rfis: Mock,
    ) -> None:
        """Related section errors raise when continue_on_error is false."""
        get_submittal.return_value = Submittal(id=20, number="27", title="Door hardware")
        list_rfis.side_effect = RuntimeError("stop")

        with TemporaryDirectory() as temporary_directory:
            with self.assertRaisesRegex(RuntimeError, "stop"):
                build_enhanced_submittal_package(
                    352338,
                    submittal_id=20,
                    output_dir=temporary_directory,
                    related_sections=["rfis"],
                    continue_on_error=False,
                )


if __name__ == "__main__":
    unittest.main()
