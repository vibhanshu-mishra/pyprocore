"""Built-in safe golden datasets for deterministic local PyProcore evals."""

from __future__ import annotations

from typing import Any

from pyprocore.evals.datasets import DATASET_SCHEMA_VERSION, load_golden_dataset_from_dict
from pyprocore.evals.model_response_suites import get_model_response_dataset_payloads
from pyprocore.evals.models import GoldenDataset
from pyprocore.evals.workflow_suites import get_workflow_dataset_payloads


def list_builtin_dataset_names() -> list[str]:
    """Return names for bundled local golden datasets."""
    return sorted(_builtin_dataset_payloads().keys())


def get_builtin_dataset(name: str) -> GoldenDataset:
    """Return one bundled local golden dataset by name.

    Args:
        name: Built-in dataset name.

    Raises:
        ValueError: If the dataset name is unknown.

    Returns:
        Validated golden dataset.
    """
    payloads = _builtin_dataset_payloads()
    if name not in payloads:
        raise ValueError(f"Unknown built-in golden dataset: {name}")
    return load_golden_dataset_from_dict(payloads[name])


def get_all_builtin_datasets() -> list[GoldenDataset]:
    """Return all bundled local golden datasets."""
    return [get_builtin_dataset(name) for name in list_builtin_dataset_names()]


def _dataset(
    name: str,
    description: str,
    cases: list[dict[str, Any]],
    *,
    tags: list[str],
) -> dict[str, Any]:
    """Build one static dataset payload."""
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


def _builtin_dataset_payloads() -> dict[str, dict[str, Any]]:
    """Return static safe built-in dataset payloads."""
    payloads = {
        "golden_agent_manifest_basic": _dataset(
            "golden_agent_manifest_basic",
            "Validate a placeholder agent manifest shape.",
            [
                {
                    "id": "agent_manifest_has_safety_flags",
                    "case_type": "agent_manifest",
                    "description": "Agent manifest exposes discovery-only safety metadata.",
                    "input": {
                        "artifact_name": "agent_manifest",
                        "artifact": {
                            "name": "pyprocore-agent",
                            "version": "2.2.0",
                            "safety": {
                                "tool_execution_enabled": False,
                                "mcp_execution_enabled": False,
                            },
                            "tools": [{"name": "procore.find_rfi"}],
                        },
                    },
                    "expected": {
                        "required_keys": [
                            "name",
                            "version",
                            "safety.tool_execution_enabled",
                            "safety.mcp_execution_enabled",
                        ],
                        "required_values": {
                            "safety.tool_execution_enabled": False,
                            "safety.mcp_execution_enabled": False,
                        },
                        "manifest_required_keys": ["name", "version", "safety"],
                    },
                }
            ],
            tags=["agent", "manifest"],
        ),
        "golden_ai_workflow_package_basic": _dataset(
            "golden_ai_workflow_package_basic",
            "Validate local model-agnostic AI workflow package metadata.",
            [
                {
                    "id": "ai_workflow_package_is_local_only",
                    "case_type": "ai_workflow_package",
                    "description": "AI package includes prompts and local-only safety notes.",
                    "input": {
                        "artifact_name": "ai_workflow_package",
                        "artifact": {
                            "package_name": "sample_rfi_review_pack",
                            "mode": "model_agnostic_local_files",
                            "prompts": [{"name": "rfi_review", "text": "Review placeholder RFI."}],
                            "safety": {"external_model_calls": False},
                        },
                    },
                    "expected": {
                        "required_keys": ["package_name", "mode", "safety.external_model_calls"],
                        "required_values": {"safety.external_model_calls": False},
                        "contains_text": ["model_agnostic_local_files"],
                    },
                }
            ],
            tags=["ai-workflows", "local"],
        ),
        "golden_async_batch_plan_basic": _dataset(
            "golden_async_batch_plan_basic",
            "Validate a safe placeholder async batch plan.",
            [
                {
                    "id": "async_batch_plan_is_dry_run_friendly",
                    "case_type": "async_batch_plan",
                    "description": "Async batch plan keeps resource reads local and explicit.",
                    "input": {
                        "artifact_name": "async_batch_plan",
                        "artifact": {
                            "plan_name": "sample_batch_plan",
                            "company_id": "placeholder-company",
                            "project_ids": ["placeholder-project"],
                            "resources": ["rfis", "submittals"],
                            "dry_run": True,
                        },
                    },
                    "expected": {
                        "required_keys": ["plan_name", "project_ids", "resources", "dry_run"],
                        "required_values": {"dry_run": True},
                    },
                }
            ],
            tags=["async", "batch"],
        ),
        "golden_export_rows_basic": _dataset(
            "golden_export_rows_basic",
            "Validate placeholder export row shape.",
            [
                {
                    "id": "export_rows_have_stable_columns",
                    "case_type": "export_rows",
                    "description": "Rows include id, number, title, and status columns.",
                    "input": {
                        "artifact_name": "rfi_export_rows",
                        "artifact": [
                            {
                                "id": "sample-rfi-1",
                                "number": "RFI-001",
                                "title": "Sample question",
                                "status": "open",
                            },
                            {
                                "id": "sample-rfi-2",
                                "number": "RFI-002",
                                "title": "Sample answer",
                                "status": "closed",
                            },
                        ],
                    },
                    "expected": {
                        "row_count": 2,
                        "required_keys": ["0.id", "0.number", "1.title"],
                    },
                }
            ],
            tags=["exports", "rows"],
        ),
        "golden_plugin_config_basic": _dataset(
            "golden_plugin_config_basic",
            "Validate plugin configuration remains metadata-only.",
            [
                {
                    "id": "plugin_config_is_metadata_only",
                    "case_type": "plugin_config",
                    "description": "Plugin config has safety policy and no execution fields.",
                    "input": {
                        "artifact_name": "plugin_config",
                        "artifact": {
                            "config_version": "1",
                            "enabled_plugins": ["csv_exporter_plugin"],
                            "safety_policy": "metadata_only",
                            "notes": ["Configuration stores preferences only."],
                        },
                    },
                    "expected": {
                        "required_keys": ["config_version", "enabled_plugins", "safety_policy"],
                        "required_values": {"safety_policy": "metadata_only"},
                    },
                }
            ],
            tags=["plugins", "config"],
        ),
        "golden_plugin_manifest_basic": _dataset(
            "golden_plugin_manifest_basic",
            "Validate plugin manifest remains metadata-only.",
            [
                {
                    "id": "plugin_manifest_is_metadata_only",
                    "case_type": "plugin_manifest",
                    "description": "Plugin manifest declares metadata-only safety.",
                    "input": {
                        "artifact_name": "plugin_manifest",
                        "artifact": {
                            "name": "csv_exporter_plugin",
                            "version": "1.0.0",
                            "capabilities": ["exporter"],
                            "safety_level": "metadata_only",
                            "enabled_by_default": False,
                        },
                    },
                    "expected": {
                        "required_keys": ["name", "version", "capabilities", "safety_level"],
                        "required_values": {"safety_level": "metadata_only"},
                        "manifest_required_keys": ["name", "version", "capabilities"],
                    },
                }
            ],
            tags=["plugins", "manifest"],
        ),
        "golden_safety_boundaries_basic": _dataset(
            "golden_safety_boundaries_basic",
            "Validate local-only safety boundary language.",
            [
                {
                    "id": "safety_boundary_disables_execution",
                    "case_type": "safety_boundary",
                    "description": "Safety text states tools and plugin execution are disabled.",
                    "input": {
                        "artifact_name": "safety_boundary",
                        "artifact": (
                            "Local deterministic evals do not call Procore, do not call "
                            "external models, do not execute tools, and do not execute plugins."
                        ),
                    },
                    "expected": {
                        "contains_text": ["do not call Procore", "do not execute tools"],
                        "does_not_contain_text": ["client_secret"],
                    },
                }
            ],
            tags=["safety"],
        ),
    }
    payloads.update(get_workflow_dataset_payloads())
    payloads.update(get_model_response_dataset_payloads())
    return payloads
