"""Unit tests for the local workflow automation runner."""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import Mock, patch

from pyprocore.core.exceptions import ValidationError
from pyprocore.workflows.automation_runner import (
    list_available_workflows,
    load_workflow_plan,
    run_workflow_plan,
    validate_workflow_plan,
)


class AutomationRunnerTestCase(unittest.TestCase):
    """Validate local workflow plan loading, validation, and execution."""

    def test_load_json_plan(self) -> None:
        """JSON workflow plans load into typed models."""
        with TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "workflow.json"
            path.write_text(
                json.dumps(
                    {
                        "name": "daily-project-export",
                        "defaults": {"project_id": 123},
                        "steps": [
                            {
                                "id": "sync",
                                "workflow": "sync_rfis",
                                "options": {"output_dir": "out"},
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            plan = load_workflow_plan(path)

        self.assertEqual(plan.name, "daily-project-export")
        self.assertEqual(plan.steps[0].workflow, "sync_rfis")

    def test_invalid_json_plan_gives_friendly_error(self) -> None:
        """Malformed JSON plans raise SDK validation errors."""
        with TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "workflow.json"
            path.write_text("{not json", encoding="utf-8")

            with self.assertRaisesRegex(ValidationError, "JSON is invalid"):
                load_workflow_plan(path)

    def test_yaml_plan_reports_optional_support_message(self) -> None:
        """YAML plans fail clearly when YAML support is not enabled."""
        with TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "workflow.yaml"
            path.write_text("name: workflow", encoding="utf-8")

            with self.assertRaisesRegex(ValidationError, "YAML workflow plans are not enabled"):
                load_workflow_plan(path)

    def test_validate_required_fields_and_enabled_steps(self) -> None:
        """Plans require at least one enabled step."""
        with self.assertRaisesRegex(ValidationError, "at least one enabled step"):
            validate_workflow_plan(
                {
                    "name": "disabled",
                    "steps": [
                        {"id": "one", "workflow": "sync_rfis", "enabled": False},
                    ],
                }
            )

    def test_validate_duplicate_step_ids(self) -> None:
        """Duplicate step IDs are rejected."""
        with self.assertRaisesRegex(ValidationError, "unique"):
            validate_workflow_plan(
                {
                    "name": "duplicates",
                    "steps": [
                        {"id": "one", "workflow": "sync_rfis"},
                        {"id": "one", "workflow": "sync_submittals"},
                    ],
                }
            )

    def test_validate_unknown_workflow(self) -> None:
        """Unsupported workflow names are rejected."""
        with self.assertRaisesRegex(ValidationError, "Unsupported workflow"):
            validate_workflow_plan(
                {
                    "name": "unknown",
                    "steps": [{"id": "one", "workflow": "not_real"}],
                }
            )

    def test_validate_bad_depends_on(self) -> None:
        """Dependencies must reference earlier known steps."""
        with self.assertRaisesRegex(ValidationError, "unknown step"):
            validate_workflow_plan(
                {
                    "name": "bad-dependency",
                    "steps": [
                        {
                            "id": "one",
                            "workflow": "sync_rfis",
                            "depends_on": ["missing"],
                        }
                    ],
                }
            )

        with self.assertRaisesRegex(ValidationError, "earlier steps"):
            validate_workflow_plan(
                {
                    "name": "future-dependency",
                    "steps": [
                        {
                            "id": "two",
                            "workflow": "sync_submittals",
                            "depends_on": ["one"],
                        },
                        {"id": "one", "workflow": "sync_rfis"},
                    ],
                }
            )

    def test_list_available_workflows_includes_phase_5a_names(self) -> None:
        """The runner lists supported existing workflows."""
        workflows = list_available_workflows()

        self.assertIn("project_context", workflows)
        self.assertIn("ai_review_export", workflows)
        self.assertIn("sync_rfis", workflows)

    def test_dry_run_resolves_placeholders_without_executing(self) -> None:
        """Dry runs resolve placeholders and avoid workflow execution."""
        workflow = Mock(return_value=SimpleNamespace(output_dir=Path("should-not-run")))
        with TemporaryDirectory() as temporary_directory:
            plan = {
                "name": "dry-run",
                "defaults": {"project_id": 123, "output_root": str(Path(temporary_directory))},
                "steps": [
                    {
                        "id": "context",
                        "workflow": "project_context",
                        "options": {"output_dir": "{output_root}/context"},
                    },
                    {
                        "id": "export",
                        "workflow": "ai_review_export",
                        "depends_on": ["context"],
                        "options": {
                            "package_dir": "{steps.context.output_dir}",
                            "output_dir": "{output_root}/ai-export",
                        },
                    },
                ],
            }

            with patch.dict(
                "pyprocore.workflows.automation_runner.WORKFLOW_DISPATCH",
                {"project_context": workflow, "ai_review_export": workflow},
            ):
                result = run_workflow_plan(plan, dry_run=True)

        workflow.assert_not_called()
        self.assertEqual(result.status, "skipped")
        self.assertEqual(result.manifest.steps[0].output_dir, Path(temporary_directory) / "context")
        self.assertEqual(
            result.manifest.steps[1].options["package_dir"],
            Path(temporary_directory) / "context",
        )

    def test_unresolved_placeholder_fails_clearly(self) -> None:
        """Missing placeholders become step errors in the manifest."""
        with TemporaryDirectory() as temporary_directory:
            result = run_workflow_plan(
                {
                    "name": "missing-placeholder",
                    "steps": [
                        {
                            "id": "one",
                            "workflow": "ai_review_export",
                            "options": {"package_dir": "{missing.value}"},
                        }
                    ],
                },
                output_dir=Path(temporary_directory),
            )

        self.assertEqual(result.status, "failed")
        self.assertIn("Could not resolve workflow placeholder", result.manifest.errors[0])

    def test_run_executes_steps_in_order_and_writes_outputs(self) -> None:
        """Successful runs execute steps in order and write run artifacts."""
        calls: list[str] = []

        def fake_sync(project_id: int, output_dir: str) -> SimpleNamespace:
            calls.append(f"sync:{project_id}")
            root = Path(output_dir)
            return SimpleNamespace(
                output_dir=root,
                manifest_path=root / "manifest.json",
                summary_path=root / "summary.md",
                warnings=[],
                errors=[],
            )

        with TemporaryDirectory() as temporary_directory:
            output_dir = Path(temporary_directory) / "run"
            plan = {
                "name": "ordered",
                "defaults": {"project_id": 123},
                "steps": [
                    {
                        "id": "one",
                        "workflow": "sync_rfis",
                        "options": {"output_dir": str(output_dir / "rfis")},
                    },
                    {
                        "id": "two",
                        "workflow": "sync_submittals",
                        "options": {"output_dir": str(output_dir / "submittals")},
                    },
                ],
            }

            with patch.dict(
                "pyprocore.workflows.automation_runner.WORKFLOW_DISPATCH",
                {"sync_rfis": fake_sync, "sync_submittals": fake_sync},
            ):
                result = run_workflow_plan(plan, output_dir=output_dir)

            self.assertTrue((output_dir / "run_manifest.json").exists())
            self.assertTrue((output_dir / "run_summary.md").exists())
            self.assertTrue((output_dir / "plan_resolved.json").exists())

        self.assertEqual(calls, ["sync:123", "sync:123"])
        self.assertEqual(result.status, "completed")

    def test_dependency_failure_skips_dependent_step(self) -> None:
        """Dependent steps are skipped when their dependency fails."""
        failing = Mock(side_effect=ValidationError("bad step"))
        dependent = Mock(return_value=SimpleNamespace(output_dir=Path("out")))

        with TemporaryDirectory() as temporary_directory:
            with patch.dict(
                "pyprocore.workflows.automation_runner.WORKFLOW_DISPATCH",
                {"sync_rfis": failing, "sync_submittals": dependent},
            ):
                result = run_workflow_plan(
                    {
                        "name": "dependency",
                        "defaults": {"project_id": 123},
                        "steps": [
                            {
                                "id": "one",
                                "workflow": "sync_rfis",
                                "options": {"output_dir": "out/rfis"},
                            },
                            {
                                "id": "two",
                                "workflow": "sync_submittals",
                                "depends_on": ["one"],
                                "options": {"output_dir": "out/submittals"},
                            },
                        ],
                    },
                    output_dir=Path(temporary_directory),
                )

        dependent.assert_not_called()
        self.assertEqual(result.manifest.steps[0].status, "failed")
        self.assertEqual(result.manifest.steps[1].status, "skipped")

    def test_continue_on_error_allows_independent_later_step(self) -> None:
        """Independent later steps can run after a failure when configured."""
        failing = Mock(side_effect=ValidationError("bad step"))
        independent = Mock(return_value=SimpleNamespace(output_dir=Path("out")))

        with TemporaryDirectory() as temporary_directory:
            with patch.dict(
                "pyprocore.workflows.automation_runner.WORKFLOW_DISPATCH",
                {"sync_rfis": failing, "sync_submittals": independent},
            ):
                result = run_workflow_plan(
                    {
                        "name": "continue",
                        "defaults": {"project_id": 123},
                        "steps": [
                            {
                                "id": "one",
                                "workflow": "sync_rfis",
                                "options": {"output_dir": "out/rfis"},
                            },
                            {
                                "id": "two",
                                "workflow": "sync_submittals",
                                "options": {"output_dir": "out/submittals"},
                            },
                        ],
                    },
                    output_dir=Path(temporary_directory),
                    continue_on_error=True,
                )

        independent.assert_called_once()
        self.assertEqual(result.status, "failed")
        self.assertEqual(result.manifest.steps[1].status, "completed")

    def test_fail_fast_skips_independent_later_step(self) -> None:
        """Fail-fast mode stops after a failed step."""
        failing = Mock(side_effect=ValidationError("bad step"))
        independent = Mock(return_value=SimpleNamespace(output_dir=Path("out")))

        with TemporaryDirectory() as temporary_directory:
            with patch.dict(
                "pyprocore.workflows.automation_runner.WORKFLOW_DISPATCH",
                {"sync_rfis": failing, "sync_submittals": independent},
            ):
                result = run_workflow_plan(
                    {
                        "name": "fail-fast",
                        "defaults": {"project_id": 123},
                        "steps": [
                            {
                                "id": "one",
                                "workflow": "sync_rfis",
                                "options": {"output_dir": "out/rfis"},
                            },
                            {
                                "id": "two",
                                "workflow": "sync_submittals",
                                "options": {"output_dir": "out/submittals"},
                            },
                        ],
                    },
                    output_dir=Path(temporary_directory),
                    continue_on_error=False,
                )

        independent.assert_not_called()
        self.assertEqual(result.manifest.steps[1].status, "skipped")

    def test_unknown_step_option_fails_clearly(self) -> None:
        """Unknown explicit options are not silently ignored."""

        def fake_workflow(project_id: int, output_dir: str) -> SimpleNamespace:
            return SimpleNamespace(output_dir=Path(output_dir))

        with TemporaryDirectory() as temporary_directory:
            with patch.dict(
                "pyprocore.workflows.automation_runner.WORKFLOW_DISPATCH",
                {"sync_rfis": fake_workflow},
            ):
                result = run_workflow_plan(
                    {
                        "name": "unknown-option",
                        "defaults": {"project_id": 123},
                        "steps": [
                            {
                                "id": "one",
                                "workflow": "sync_rfis",
                                "options": {"output_dir": "out", "typo": True},
                            }
                        ],
                    },
                    output_dir=Path(temporary_directory),
                )

        self.assertEqual(result.status, "failed")
        self.assertIn("unsupported option", result.manifest.errors[0])


if __name__ == "__main__":
    unittest.main()
