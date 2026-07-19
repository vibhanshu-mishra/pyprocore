"""Workflow-specific built-in golden dataset payloads for local evals."""

from __future__ import annotations

from typing import Any

from pyprocore.evals.datasets import DATASET_SCHEMA_VERSION


def get_workflow_dataset_payloads() -> dict[str, dict[str, Any]]:
    """Return workflow-specific built-in golden dataset payloads."""
    return {
        "ai_workflow_package_golden": _dataset(
            "ai_workflow_package_golden",
            "Validate model-agnostic AI workflow package artifacts.",
            [
                _case(
                    "ai_package_has_expected_sections",
                    "ai_workflow_package",
                    {
                        "title": "Sample AI Review Package",
                        "purpose": "Prepare local project context for human review.",
                        "inputs": ["sample-rfis.jsonl", "sample-submittals.jsonl"],
                        "context_documents": ["sample-specifications-index.json"],
                        "prompt_templates": [
                            {
                                "name": "grounded_review",
                                "text": "Use only provided context. Do not invent facts.",
                            }
                        ],
                        "safety_checklist": ["Do not invent facts", "Cite source labels"],
                        "output_expectations": {
                            "format": "markdown",
                            "human_review_required": True,
                        },
                    },
                    expected={
                        "required_keys": [
                            "title",
                            "purpose",
                            "inputs",
                            "context_documents",
                            "prompt_templates",
                            "safety_checklist",
                            "output_expectations",
                        ],
                        "required_phrases": ["do not invent facts", "human_review_required"],
                        "placeholder_only": True,
                        "no_mutation_instructions": True,
                        "no_secret_like_values": True,
                    },
                ),
                _case(
                    "ai_vector_manifest_is_local_and_redacted",
                    "ai_workflow_package",
                    {
                        "name": "sample_vector_export_manifest",
                        "chunks": [
                            {
                                "chunk_id": "sample-chunk-001",
                                "source_label": "sample-spec-section-01",
                                "metadata": {
                                    "resource": "specifications",
                                    "project_id": "placeholder",
                                },
                            }
                        ],
                        "external_model_calls": False,
                    },
                    expected={
                        "required_keys": [
                            "name",
                            "chunks.0.chunk_id",
                            "chunks.0.source_label",
                            "chunks.0.metadata",
                            "external_model_calls",
                        ],
                        "required_values": {"external_model_calls": False},
                        "manifest_required_keys": ["name", "chunks"],
                        "placeholder_only": True,
                    },
                ),
            ],
            tags=["phase13b", "ai-workflows"],
        ),
        "async_batch_golden": _dataset(
            "async_batch_golden",
            "Validate async batch plans and manifests without live calls.",
            [
                _case(
                    "batch_plan_is_dry_run_safe",
                    "async_batch_plan",
                    {
                        "plan_name": "sample_nightly_batch",
                        "company_id": "placeholder-company",
                        "project_ids": ["placeholder-project-a", "placeholder-project-b"],
                        "resources": ["rfis", "submittals", "specifications"],
                        "output_dir": "./exports/sample-batch",
                        "max_concurrency": 3,
                        "dry_run": True,
                        "continue_on_error": True,
                    },
                    expected={
                        "required_keys": [
                            "company_id",
                            "project_ids",
                            "resources",
                            "output_dir",
                            "max_concurrency",
                            "dry_run",
                        ],
                        "required_values": {"dry_run": True, "continue_on_error": True},
                        "placeholder_only": True,
                        "no_secret_like_values": True,
                    },
                ),
                _case(
                    "batch_manifest_tracks_partial_failure",
                    "async_batch_manifest",
                    {
                        "name": "sample_batch_manifest",
                        "status": "completed_with_warnings",
                        "dry_run": True,
                        "results": [
                            {
                                "project_id": "placeholder-project-a",
                                "resource": "rfis",
                                "status": "success",
                                "output_path": "./exports/sample-batch/project-a/rfis.jsonl",
                                "count": 2,
                                "warnings": [],
                                "errors": [],
                            },
                            {
                                "project_id": "placeholder-project-b",
                                "resource": "submittals",
                                "status": "failed",
                                "output_path": "./exports/sample-batch/project-b/submittals.jsonl",
                                "count": 0,
                                "warnings": ["sample permission warning"],
                                "errors": ["redacted sample error"],
                            },
                        ],
                    },
                    expected={
                        "manifest_required_keys": ["name", "status", "results"],
                        "manifest_status": "completed_with_warnings",
                        "output_dir": "./exports/sample-batch",
                        "output_paths": [
                            "./exports/sample-batch/project-a/rfis.jsonl",
                            "./exports/sample-batch/project-b/submittals.jsonl",
                        ],
                        "placeholder_only": True,
                        "no_secret_like_values": True,
                    },
                ),
            ],
            tags=["phase13b", "async", "batch"],
        ),
        "async_export_golden": _dataset(
            "async_export_golden",
            "Validate async export rows and export manifests.",
            [
                _case(
                    "async_export_rows_have_csv_jsonl_shape",
                    "export_rows",
                    [
                        {
                            "id": "sample-row-001",
                            "resource": "rfis",
                            "number": "RFI-001",
                            "title": "Sample coordination question",
                            "status": "open",
                        },
                        {
                            "id": "sample-row-002",
                            "resource": "submittals",
                            "number": "SUB-001",
                            "title": "Sample product data",
                            "status": "review",
                        },
                    ],
                    expected={
                        "row_count": 2,
                        "expected_fields": ["id", "resource", "number", "title", "status"],
                        "placeholder_only": True,
                        "no_secret_like_values": True,
                    },
                ),
                _case(
                    "async_export_manifest_stays_under_output_dir",
                    "async_export_manifest",
                    {
                        "name": "sample_async_export_manifest",
                        "resource": "rfis",
                        "output_path": "./exports/sample-async/rfis.jsonl",
                        "record_count": 2,
                        "warnings": [],
                        "errors": ["redacted sample warning only"],
                        "dry_run": True,
                    },
                    expected={
                        "manifest_required_keys": [
                            "name",
                            "resource",
                            "output_path",
                            "record_count",
                            "warnings",
                            "errors",
                            "dry_run",
                        ],
                        "output_dir": "./exports/sample-async",
                        "output_paths": ["./exports/sample-async/rfis.jsonl"],
                        "required_values": {"dry_run": True},
                        "placeholder_only": True,
                        "no_secret_like_values": True,
                    },
                ),
            ],
            tags=["phase13b", "async", "exports"],
        ),
        "plugin_config_golden": _dataset(
            "plugin_config_golden",
            "Validate plugin configuration and extension-pack metadata fixtures.",
            [
                _case(
                    "plugin_config_is_metadata_only",
                    "plugin_config",
                    {
                        "config_version": "1",
                        "enabled_plugins": ["sample_exporter"],
                        "hooks_enabled_from_config": False,
                        "preferences": {"default_output": "./exports/sample-plugin"},
                    },
                    expected={
                        "required_keys": [
                            "config_version",
                            "enabled_plugins",
                            "hooks_enabled_from_config",
                        ],
                        "required_values": {
                            "hooks_enabled_from_config": False,
                        },
                        "output_dir": "./exports",
                        "output_paths": ["./exports/sample-plugin"],
                        "placeholder_only": True,
                        "no_secret_like_values": True,
                    },
                ),
                _case(
                    "extension_pack_manifest_is_metadata_only",
                    "extension_pack",
                    {
                        "name": "sample_extension_pack",
                        "version": "0.1.0",
                        "plugins": ["sample_exporter"],
                        "safety_level": "metadata_only",
                        "setup_required": False,
                    },
                    expected={
                        "manifest_required_keys": ["name", "version", "plugins", "safety_level"],
                        "required_values": {
                            "safety_level": "metadata_only",
                            "setup_required": False,
                        },
                        "placeholder_only": True,
                        "no_secret_like_values": True,
                    },
                ),
            ],
            tags=["phase13b", "plugins", "config"],
        ),
        "plugin_metadata_golden": _dataset(
            "plugin_metadata_golden",
            "Validate plugin manifests and hook metadata remain local and inert.",
            [
                _case(
                    "plugin_manifest_uses_allowed_capabilities",
                    "plugin_manifest",
                    {
                        "name": "sample_exporter",
                        "version": "0.1.0",
                        "description": "Sample metadata-only export extension.",
                        "capabilities": ["exporter", "formatter"],
                        "safety_level": "metadata_only",
                        "enabled_by_default": False,
                        "hooks": [{"name": "format_rows", "type": "metadata"}],
                    },
                    expected={
                        "manifest_required_keys": [
                            "name",
                            "version",
                            "description",
                            "capabilities",
                            "safety_level",
                        ],
                        "allowed_capabilities": ["exporter", "formatter", "validator"],
                        "allowed_hook_types": ["metadata", "local_registered_callable"],
                        "required_values": {"enabled_by_default": False},
                        "placeholder_only": True,
                        "no_secret_like_values": True,
                    },
                ),
                _case(
                    "plugin_scaffold_uses_placeholder_values",
                    "plugin_manifest",
                    {
                        "name": "sample_scaffold",
                        "version": "0.1.0",
                        "description": "Generated safe placeholder plugin metadata.",
                        "capabilities": ["validator"],
                        "safety_level": "metadata_only",
                        "files": ["sample_plugin/README.md", "sample_plugin/manifest.json"],
                    },
                    expected={
                        "manifest_required_keys": ["name", "version", "capabilities"],
                        "allowed_capabilities": ["exporter", "formatter", "validator"],
                        "placeholder_only": True,
                        "no_secret_like_values": True,
                    },
                ),
            ],
            tags=["phase13b", "plugins", "metadata"],
        ),
        "rfi_workflow_golden": _dataset(
            "rfi_workflow_golden",
            "Validate RFI workflow exports, packages, and prompt artifacts.",
            [
                _case(
                    "rfi_export_rows_have_expected_fields",
                    "export_rows",
                    [
                        {
                            "id": "sample-rfi-001",
                            "number": "RFI-001",
                            "title": "Sample wall detail question",
                            "status": "open",
                            "responsible_contractor": "Sample Contractor",
                            "assignee": "Sample Reviewer",
                            "due_date": "2026-01-15",
                        }
                    ],
                    expected={
                        "row_count": 1,
                        "expected_fields": [
                            "id",
                            "number",
                            "title",
                            "status",
                            "responsible_contractor",
                            "assignee",
                            "due_date",
                        ],
                        "placeholder_only": True,
                        "no_secret_like_values": True,
                    },
                ),
                _case(
                    "rfi_package_contains_context_without_answers",
                    "rfi_workflow_package",
                    {
                        "package_name": "sample_rfi_package",
                        "question": "Sample question about coordination.",
                        "status": "open",
                        "responsible_contractor": "Sample Contractor",
                        "assignee": "Sample Reviewer",
                        "due_date": "2026-01-15",
                        "references": ["sample-drawing-A101"],
                        "model_generated_answer": None,
                    },
                    expected={
                        "required_keys": [
                            "question",
                            "status",
                            "responsible_contractor",
                            "assignee",
                            "due_date",
                            "references",
                        ],
                        "required_values": {"model_generated_answer": None},
                        "placeholder_only": True,
                        "no_mutation_instructions": True,
                    },
                ),
                _case(
                    "rfi_prompt_package_is_grounded",
                    "ai_workflow_package",
                    {
                        "name": "sample_rfi_prompt_package",
                        "prompt": "Use only provided RFI context. Do not invent facts.",
                        "safety": ["ground answers in provided sources", "human review required"],
                    },
                    expected={
                        "required_phrases": [
                            "use only provided rfi context",
                            "do not invent facts",
                        ],
                        "placeholder_only": True,
                        "no_mutation_instructions": True,
                    },
                ),
            ],
            tags=["phase13b", "rfis", "workflows"],
        ),
        "safety_boundaries_golden": _dataset(
            "safety_boundaries_golden",
            "Validate cross-SDK local deterministic safety boundaries.",
            [
                _case(
                    "agent_and_mcp_execution_remain_disabled",
                    "safety_boundary",
                    {
                        "agent_tool_execution_enabled": False,
                        "mcp_execution_enabled": False,
                        "plugin_execution_from_config_enabled": False,
                        "remote_dataset_fetching_enabled": False,
                        "external_model_calls_enabled": False,
                        "mode": "local deterministic placeholder fixtures",
                    },
                    expected={
                        "required_values": {
                            "agent_tool_execution_enabled": False,
                            "mcp_execution_enabled": False,
                            "plugin_execution_from_config_enabled": False,
                            "remote_dataset_fetching_enabled": False,
                            "external_model_calls_enabled": False,
                        },
                        "placeholder_only": True,
                        "no_secret_like_values": True,
                    },
                ),
                _case(
                    "read_only_workflow_boundaries_are_declared",
                    "safety_boundary",
                    {
                        "async_exports": "read-only local export fixtures",
                        "financials": "read-only sample coverage",
                        "contracts": "read-only sample coverage",
                        "writes_enabled": False,
                        "local_reports_only": True,
                    },
                    expected={
                        "required_values": {"writes_enabled": False, "local_reports_only": True},
                        "required_phrases": ["read-only", "local export fixtures"],
                        "no_mutation_instructions": True,
                        "placeholder_only": True,
                    },
                ),
            ],
            tags=["phase13b", "safety"],
        ),
        "submittal_workflow_golden": _dataset(
            "submittal_workflow_golden",
            "Validate submittal workflow exports, packages, and prompt artifacts.",
            [
                _case(
                    "submittal_export_rows_have_expected_fields",
                    "export_rows",
                    [
                        {
                            "id": "sample-submittal-001",
                            "number": "SUB-001",
                            "title": "Sample product data",
                            "status": "under_review",
                            "due_date": "2026-02-15",
                            "submitter": "Sample Submitter",
                            "reviewer": "Sample Reviewer",
                            "spec_section": "Sample Section 07 00 00",
                            "ball_in_court": "Sample Reviewer",
                        }
                    ],
                    expected={
                        "row_count": 1,
                        "expected_fields": [
                            "id",
                            "number",
                            "title",
                            "status",
                            "due_date",
                            "submitter",
                            "reviewer",
                            "spec_section",
                            "ball_in_court",
                        ],
                        "placeholder_only": True,
                        "no_secret_like_values": True,
                    },
                ),
                _case(
                    "submittal_review_package_has_required_context",
                    "submittal_workflow_package",
                    {
                        "package_name": "sample_submittal_review_package",
                        "title": "Sample product data",
                        "number": "SUB-001",
                        "status": "under_review",
                        "due_date": "2026-02-15",
                        "submitter": "Sample Submitter",
                        "reviewer": "Sample Reviewer",
                        "spec_section": "Sample Section 07 00 00",
                        "ball_in_court": "Sample Reviewer",
                        "model_decision": None,
                    },
                    expected={
                        "required_keys": [
                            "title",
                            "number",
                            "status",
                            "due_date",
                            "submitter",
                            "reviewer",
                            "spec_section",
                            "ball_in_court",
                        ],
                        "required_values": {"model_decision": None},
                        "placeholder_only": True,
                        "no_mutation_instructions": True,
                    },
                ),
                _case(
                    "submittal_prompt_keeps_decisions_human",
                    "ai_workflow_package",
                    {
                        "name": "sample_submittal_prompt_package",
                        "prompt": (
                            "Ground observations in provided context. " "Human review is required."
                        ),
                        "safety": ["do not make approval decisions", "do not invent facts"],
                    },
                    expected={
                        "required_phrases": [
                            "ground observations",
                            "human review is required",
                            "do not invent facts",
                        ],
                        "forbidden_phrases": ["approve this submittal", "reject this submittal"],
                        "placeholder_only": True,
                        "no_mutation_instructions": True,
                    },
                ),
            ],
            tags=["phase13b", "submittals", "workflows"],
        ),
    }


def _dataset(
    name: str,
    description: str,
    cases: list[dict[str, Any]],
    *,
    tags: list[str],
) -> dict[str, Any]:
    """Build one workflow-specific static dataset payload."""
    return {
        "schema_version": DATASET_SCHEMA_VERSION,
        "metadata": {
            "name": name,
            "description": description,
            "tags": tags,
            "mode": "local_deterministic",
        },
        "cases": cases,
    }


def _case(
    case_id: str,
    case_type: str,
    artifact: Any,
    *,
    expected: dict[str, Any],
) -> dict[str, Any]:
    """Build one workflow-specific golden case payload."""
    return {
        "id": case_id,
        "case_type": case_type,
        "description": case_id.replace("_", " ").capitalize() + ".",
        "input": {"artifact_name": case_id, "artifact": artifact},
        "expected": expected,
    }
