"""Tests for Phase 12 model-agnostic AI workflow examples."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import pyprocore
from pyprocore.agent import build_mcp_tool_execution_disabled_response
from pyprocore.core.exceptions import ValidationError
from pyprocore.workflows import (
    AiWorkflowInput,
    build_ai_workflow_safety_checklist,
    build_change_risk_review_prompt_pack,
    build_drawing_spec_comparison_prompt_pack,
    build_engineering_assistant_context_bundle,
    build_field_issue_summary_prompt_pack,
    build_project_qa_prompt_pack,
    build_rfi_review_prompt_pack,
    build_submittal_review_prompt_pack,
    build_vector_index_manifest,
    chunk_text_for_vector_export,
    write_ai_workflow_package,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]


class Phase12AiWorkflowsTestCase(unittest.TestCase):
    """Validate Phase 12 remains local-only, model-agnostic, and safe."""

    def read_text(self, relative_path: str) -> str:
        """Read a repository file."""
        return (PROJECT_ROOT / relative_path).read_text(encoding="utf-8")

    def test_prompt_helpers_return_serializable_prompt_models(self) -> None:
        """Prompt helpers should build local prompt objects only."""
        prompts = [
            build_rfi_review_prompt_pack({"number": "RFI-1", "title": "Question"}),
            build_submittal_review_prompt_pack({"number": "SUB-1", "title": "Product data"}),
            build_project_qa_prompt_pack("Local project summary."),
            build_drawing_spec_comparison_prompt_pack("Drawing note.", "Spec note."),
            build_engineering_assistant_context_bundle("Engineering context."),
            build_field_issue_summary_prompt_pack("Field issue notes."),
            build_change_risk_review_prompt_pack("Change context."),
        ]

        for prompt in prompts:
            dumped = prompt.model_dump(mode="json")
            self.assertIn("user_prompt", dumped)
            self.assertIn("Do not claim authority", prompt.system_context)
            self.assertGreater(len(prompt.checklist), 0)

    def test_vector_manifest_and_chunking_are_deterministic(self) -> None:
        """Vector helpers should chunk local text without external dependencies."""
        text = " ".join(f"placeholder-{index}" for index in range(40))
        chunks = chunk_text_for_vector_export(
            text,
            source_name="sample.md",
            chunk_size=80,
            overlap=10,
            metadata={"kind": "sample"},
        )
        manifest = build_vector_index_manifest(
            text,
            source_name="sample.md",
            chunk_size=80,
            overlap=10,
        )

        self.assertGreater(len(chunks), 1)
        self.assertEqual(chunks[0].id, "sample-md-0001")
        self.assertEqual(chunks[0].metadata["kind"], "sample")
        self.assertEqual(manifest.chunk_count, len(manifest.chunks))
        self.assertIn("model-agnostic", " ".join(manifest.notes))

    def test_vector_chunking_handles_edge_cases(self) -> None:
        """Chunking should handle blank text, fallback slugs, and hard boundaries."""
        self.assertEqual(chunk_text_for_vector_export("   "), [])

        hard_boundary_chunks = chunk_text_for_vector_export(
            "abcdefghij" * 4,
            source_name="!!!",
            chunk_size=11,
            overlap=2,
        )
        newline_boundary_chunks = chunk_text_for_vector_export(
            "alpha beta\ngamma delta epsilon",
            source_name="notes.md",
            chunk_size=18,
            overlap=3,
        )

        self.assertGreater(len(hard_boundary_chunks), 1)
        self.assertEqual(hard_boundary_chunks[0].id, "source-0001")
        self.assertGreater(len(newline_boundary_chunks), 1)
        self.assertLessEqual(len(newline_boundary_chunks[0].text), 18)

    def test_chunk_validation_rejects_invalid_settings(self) -> None:
        """Invalid chunk settings should raise SDK validation errors."""
        with self.assertRaises(ValidationError):
            chunk_text_for_vector_export("text", chunk_size=0)
        with self.assertRaises(ValidationError):
            chunk_text_for_vector_export("text", chunk_size=10, overlap=-1)
        with self.assertRaises(ValidationError):
            chunk_text_for_vector_export("text", chunk_size=10, overlap=10)

    def test_write_ai_workflow_package_uses_local_files_only(self) -> None:
        """Package writer should create local prompt/checklist files."""
        workflow_input = AiWorkflowInput(
            title="Local Placeholder Package",
            workflow="rfi_review",
            summary="Placeholder local context.",
            records=[{"number": "RFI-PLACEHOLDER", "title": "Question"}],
        )
        with tempfile.TemporaryDirectory() as tmp:
            result = write_ai_workflow_package(workflow_input, tmp)
            self.assertTrue(result.manifest_path)
            self.assertTrue((Path(tmp) / "prompt.md").exists())
            self.assertTrue((Path(tmp) / "safety_checklist.md").exists())
            manifest = json.loads((Path(tmp) / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["workflow"], "rfi_review")

    def test_write_ai_workflow_package_rejects_existing_output_without_overwrite(
        self,
    ) -> None:
        """Package writer should avoid overwriting existing output by default."""
        workflow_input = AiWorkflowInput(
            title="Local Placeholder Package",
            workflow="rfi_review",
            summary="Placeholder local context.",
        )
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "existing.txt").write_text("existing", encoding="utf-8")

            with self.assertRaises(ValidationError):
                write_ai_workflow_package(workflow_input, tmp)

    def test_write_ai_workflow_package_supports_all_phase12_workflow_kinds(self) -> None:
        """Package writer should route every Phase 12 workflow to a local prompt."""
        workflow_kinds = (
            "submittal_review",
            "project_qa",
            "drawing_spec_comparison",
            "field_issue_summary",
            "change_risk_review",
            "engineering_assistant_context",
            "vector_export",
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for workflow in workflow_kinds:
                workflow_input = AiWorkflowInput(
                    title=f"{workflow} package",
                    workflow=workflow,
                    summary="Placeholder local context.",
                    records=[{"number": None, "title": None}],
                    notes=["Human review required."],
                )

                result = write_ai_workflow_package(
                    workflow_input,
                    root / workflow,
                    overwrite=True,
                )

                self.assertEqual(result.workflow, workflow)
                self.assertTrue(result.manifest_path)

    def test_safety_checklist_preserves_boundaries(self) -> None:
        """Safety checklist should state Phase 12 boundaries clearly."""
        checklist = build_ai_workflow_safety_checklist()
        boundaries = "\n".join(checklist.boundaries)

        self.assertIn("does not call external AI/model APIs", boundaries)
        self.assertIn("does not require AI framework", boundaries)
        self.assertIn("Procore tool execution remains disabled", boundaries)
        self.assertIn("MCP remains discovery-only", boundaries)

    def test_examples_131_to_140_exist_and_use_main_guards(self) -> None:
        """All Phase 12 examples should exist and be examples-check compatible."""
        for number in range(131, 141):
            matches = sorted((PROJECT_ROOT / "examples").glob(f"{number}_*.py"))
            self.assertEqual(len(matches), 1, f"Missing or duplicate example {number}")
            source = matches[0].read_text(encoding="utf-8")
            self.assertIn('if __name__ == "__main__":', source)
            self.assertNotIn("requests.", source)

    def test_templates_are_placeholder_only(self) -> None:
        """Templates should not include real project data or secrets."""
        template_dir = PROJECT_ROOT / "examples" / "ai_workflows"
        self.assertTrue(template_dir.exists())
        combined = "\n".join(path.read_text(encoding="utf-8") for path in template_dir.rglob("*"))

        self.assertIn("PLACEHOLDER", combined)
        self.assertNotIn("Authorization: Bearer", combined)
        self.assertNotIn("client_secret", combined.casefold())
        self.assertNotIn("api_key", combined.casefold())

    def test_no_required_ai_dependencies_were_added(self) -> None:
        """Runtime dependencies should not require AI frameworks or vector stores."""
        dependency_text = (
            self.read_text("pyproject.toml") + "\n" + self.read_text("requirements.txt")
        )
        forbidden = (
            "openai>=",
            "anthropic>=",
            "langchain",
            "llama-index",
            "chromadb",
            "faiss",
        )
        for marker in forbidden:
            self.assertNotIn(marker, dependency_text.casefold())

    def test_safety_script_passes(self) -> None:
        """The Phase 12 safety script should pass locally."""
        completed = subprocess.run(
            [sys.executable, "scripts/check_ai_workflow_safety.py"],
            cwd=PROJECT_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertIn("PASS", completed.stdout)

    def test_docs_and_readme_describe_phase12_as_released(self) -> None:
        """Docs should describe Phase 12 as included in the current release."""
        docs = "\n".join(
            self.read_text(path)
            for path in (
                "README.md",
                "docs/ai-workflows.md",
                "docs/project-status.md",
                "docs/roadmap.md",
                "examples/README.md",
            )
        )

        self.assertIn("Phase 12", docs)
        self.assertIn("Included in v2.3.0", docs)
        self.assertIn("does not call external AI/model APIs", docs)
        self.assertNotIn("Phase 12 is published", docs)

    def test_agent_and_mcp_execution_remain_disabled(self) -> None:
        """Phase 12 should not alter agent or MCP execution safety."""
        response = build_mcp_tool_execution_disabled_response("procore.find_rfi")

        self.assertFalse(response["metadata"]["execution_enabled"])
        self.assertTrue(response["metadata"]["discovery_only"])
        self.assertEqual(pyprocore.__version__, "2.3.0")


if __name__ == "__main__":
    unittest.main()
