"""Unit tests for local AI review export workflows."""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from pyprocore.core.exceptions import ValidationError
from pyprocore.workflows import build_ai_prompt_pack, build_ai_review_export


class AIExportWorkflowTestCase(unittest.TestCase):
    """Validate local AI review export package builders."""

    def test_build_ai_review_export_detects_rfi_package(self) -> None:
        """RFI packages produce package-aware Markdown, JSON, prompts, and checklists."""
        with TemporaryDirectory() as temporary_directory:
            package = Path(temporary_directory) / "rfi-package"
            package.mkdir()
            (package / "rfi.json").write_text(
                json.dumps({"id": 10, "number": "15", "subject": "Door hardware"}),
                encoding="utf-8",
            )
            (package / "ai").mkdir()
            (package / "ai" / "review_context.md").write_text(
                "# RFI Review Context\n\nQuestion and answer context.",
                encoding="utf-8",
            )
            (package / "attachments").mkdir()
            (package / "attachments" / "drawing.pdf").write_bytes(b"%PDF")

            result = build_ai_review_export(package)

            self.assertEqual(result.package_type, "enhanced_rfi")
            self.assertTrue(result.manifest_path.exists())
            self.assertTrue(result.ai_review_path.exists())
            self.assertIsNotNone(result.ai_review_json_path)
            self.assertIsNotNone(result.prompt_path)
            self.assertIsNotNone(result.system_context_path)
            self.assertEqual(len(result.checklist_paths), 3)
            review = result.ai_review_path.read_text(encoding="utf-8")
            self.assertIn("RFI overview", review)
            self.assertIn("Question and answer context", review)
            source_index = json.loads(result.source_index_json_path.read_text(encoding="utf-8"))
            self.assertTrue(any(item["relative_path"] == "rfi.json" for item in source_index))
            self.assertTrue(
                any(
                    item["relative_path"] == "attachments/drawing.pdf" and item["included"] is False
                    for item in source_index
                )
            )

    def test_build_ai_review_export_detects_submittal_package(self) -> None:
        """Submittal packages include submittal-specific review guidance."""
        with TemporaryDirectory() as temporary_directory:
            package = Path(temporary_directory) / "submittal-package"
            package.mkdir()
            (package / "submittal.json").write_text(
                json.dumps({"id": 20, "number": "27", "title": "Concrete mix"}),
                encoding="utf-8",
            )

            result = build_ai_review_export(package)

            self.assertEqual(result.package_type, "enhanced_submittal")
            self.assertIn(
                "Submittal overview",
                result.ai_review_path.read_text(encoding="utf-8"),
            )

    def test_build_ai_review_export_detects_project_context_package(self) -> None:
        """Project context packages are detected from project metadata."""
        with TemporaryDirectory() as temporary_directory:
            package = Path(temporary_directory) / "project-context"
            package.mkdir()
            (package / "project.json").write_text(
                json.dumps({"id": 352338, "name": "Sandbox"}),
                encoding="utf-8",
            )

            result = build_ai_review_export(package)

            self.assertEqual(result.package_type, "project_context")
            self.assertIn(
                "Project overview",
                result.ai_review_path.read_text(encoding="utf-8"),
            )

    def test_build_ai_review_export_handles_generic_package(self) -> None:
        """Unknown package shapes still produce a useful generic export."""
        with TemporaryDirectory() as temporary_directory:
            package = Path(temporary_directory) / "package"
            package.mkdir()
            (package / "notes.md").write_text("General package notes.", encoding="utf-8")

            result = build_ai_review_export(package, include_json=False)

            self.assertEqual(result.package_type, "generic")
            self.assertIsNone(result.ai_review_json_path)
            self.assertIn("Available local source files", result.ai_review_path.read_text())

    def test_build_ai_review_export_chunks_large_sources(self) -> None:
        """Large source files are split deterministically into chunk files."""
        with TemporaryDirectory() as temporary_directory:
            package = Path(temporary_directory) / "package"
            package.mkdir()
            (package / "notes.md").write_text(("Line of context\n" * 900), encoding="utf-8")

            result = build_ai_review_export(package, max_chunk_chars=1500)

            self.assertGreater(len(result.chunk_paths), 1)
            self.assertTrue(all(path.exists() for path in result.chunk_paths))
            self.assertEqual(result.chunk_paths[0].name, "chunk_001.md")
            first_chunk = result.chunk_paths[0].read_text(encoding="utf-8")
            self.assertIn("## Source: notes.md", first_chunk)

    def test_build_ai_review_export_respects_include_options(self) -> None:
        """Optional JSON, prompt, and checklist artifacts can be disabled."""
        with TemporaryDirectory() as temporary_directory:
            package = Path(temporary_directory) / "package"
            package.mkdir()
            (package / "notes.md").write_text("Notes", encoding="utf-8")

            result = build_ai_review_export(
                package,
                include_json=False,
                include_prompt=False,
                include_checklists=False,
            )

            self.assertIsNone(result.ai_review_json_path)
            self.assertIsNone(result.prompt_path)
            self.assertIsNone(result.system_context_path)
            self.assertEqual(result.checklist_paths, [])

    def test_build_ai_review_export_refuses_non_empty_output_without_overwrite(self) -> None:
        """Existing non-empty output directories require overwrite=True."""
        with TemporaryDirectory() as temporary_directory:
            package = Path(temporary_directory) / "package"
            package.mkdir()
            (package / "notes.md").write_text("Notes", encoding="utf-8")
            output = package / "ai-export"
            output.mkdir()
            (output / "old.md").write_text("old", encoding="utf-8")

            with self.assertRaises(ValidationError):
                build_ai_review_export(package)

            result = build_ai_review_export(package, overwrite=True)
            self.assertEqual(result.output_dir, output)

    def test_build_ai_review_export_validates_inputs(self) -> None:
        """Invalid package folders, chunk sizes, and formats fail clearly."""
        with TemporaryDirectory() as temporary_directory:
            package = Path(temporary_directory) / "package"
            package.mkdir()

            with self.assertRaises(ValidationError):
                build_ai_review_export(package / "missing")
            with self.assertRaises(ValidationError):
                build_ai_review_export(package, max_chunk_chars=0)
            with self.assertRaises(ValidationError):
                build_ai_review_export(package, format="html")

    def test_build_ai_prompt_pack_uses_prompt_defaults(self) -> None:
        """Prompt packs use the prompt-pack output folder and skip JSON by default."""
        with TemporaryDirectory() as temporary_directory:
            package = Path(temporary_directory) / "package"
            package.mkdir()
            (package / "notes.md").write_text("Notes", encoding="utf-8")

            result = build_ai_prompt_pack(package, review_type="rfi")

            self.assertEqual(result.output_dir, package / "ai-prompt-pack")
            self.assertIsNone(result.ai_review_json_path)
            self.assertIsNotNone(result.prompt_path)
            self.assertEqual(result.manifest.options.export_name, "rfi-prompt-pack")


if __name__ == "__main__":
    unittest.main()
