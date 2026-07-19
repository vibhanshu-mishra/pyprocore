"""Discovery-only MCP prompt templates for PyProcore."""

from __future__ import annotations

from pyprocore.mcp.models import McpPrompt, McpPromptArgument, McpPromptKind, McpSafetyBoundary


def list_mcp_prompts() -> list[McpPrompt]:
    """Return built-in local MCP prompt templates sorted by name."""
    prompts = [
        _prompt(
            "pyprocore.discovery_summary",
            "PyProcore Discovery Summary Prompt",
            "Summarize local PyProcore discovery metadata for a client or assistant.",
            McpPromptKind.SAFETY_BOUNDARY_REVIEW,
            [
                "Use only supplied PyProcore discovery metadata.",
                "Summarize available local resources, prompts, and tools with source labels.",
                "State that PyProcore MCP is discovery-only and no Procore or model call was made.",
                "Do not perform Procore actions.",
            ],
            ["discovery_manifest_json", "summary_focus"],
        ),
        _prompt(
            "rfi_review_prompt",
            "RFI Review Prompt",
            "Review a saved RFI context package using cited local evidence.",
            McpPromptKind.RFI_REVIEW,
            [
                "Use only the supplied RFI context.",
                "Ground every key conclusion in a named local source label.",
                "State limitations when evidence is missing.",
                "PyProcore MCP is discovery-only; do not perform Procore actions.",
            ],
            ["rfi_context_json", "review_question"],
        ),
        _prompt(
            "submittal_review_prompt",
            "Submittal Review Prompt",
            "Review a saved submittal context package with traceable source labels.",
            McpPromptKind.SUBMITTAL_REVIEW,
            [
                "Use only the supplied review context.",
                "Separate facts from review notes.",
                "Cite each material statement with a local source label.",
                "PyProcore MCP is discovery-only; do not perform Procore actions.",
            ],
            ["submittal_context_json", "review_focus"],
        ),
        _prompt(
            "project_context_qa_prompt",
            "Project Context Q&A Prompt",
            "Answer questions from a local project context package.",
            McpPromptKind.PROJECT_CONTEXT_QA,
            [
                "Answer only from the supplied project context.",
                "Say when the context is insufficient.",
                "Include source labels for every answer.",
                "PyProcore MCP is discovery-only metadata; it does not call Procore or models.",
            ],
            ["project_context_json", "question"],
        ),
        _prompt(
            "drawing_spec_comparison_prompt",
            "Drawing and Spec Comparison Prompt",
            "Compare saved drawing and specification context with explicit grounding.",
            McpPromptKind.DRAWING_SPEC_COMPARISON,
            [
                "Compare only the supplied drawing and specification excerpts with grounding.",
                "List agreements, conflicts, and missing evidence separately.",
                "Cite local drawing and specification labels.",
                "PyProcore MCP is discovery-only and cannot change Procore records.",
            ],
            ["drawing_context", "specification_context"],
        ),
        _prompt(
            "engineering_assistant_prompt",
            "Engineering Assistant Prompt",
            "Plan a read-only engineering review from local PyProcore context.",
            McpPromptKind.ENGINEERING_ASSISTANT,
            [
                "Use local PyProcore context as the only evidence.",
                "Prefer concise findings with source labels.",
                "Flag uncertainty and missing data clearly.",
                "PyProcore MCP is discovery-only; no tool execution is available.",
            ],
            ["context_json", "engineering_question"],
        ),
        _prompt(
            "field_issue_summary_prompt",
            "Field Issue Summary Prompt",
            "Summarize saved field issue context for review.",
            McpPromptKind.FIELD_ISSUE_SUMMARY,
            [
                "Summarize only supplied field context.",
                "Group impact, blockers, and next review questions.",
                "Cite local source labels.",
                "PyProcore MCP discovery does not call Procore.",
            ],
            ["field_context_json"],
        ),
        _prompt(
            "change_risk_review_prompt",
            "Change Risk Review Prompt",
            "Review local change-risk context without taking action.",
            McpPromptKind.CHANGE_RISK_REVIEW,
            [
                "Use only supplied contract, RFI, review item, drawing, and spec context.",
                "Separate risk signals from confirmed facts.",
                "Cite local source labels and disclose gaps.",
                "PyProcore MCP does not perform Procore actions.",
            ],
            ["risk_context_json"],
        ),
        _prompt(
            "async_export_planning_prompt",
            "Async Export Planning Prompt",
            "Plan a local async export from provided metadata.",
            McpPromptKind.ASYNC_EXPORT_PLANNING,
            [
                "Use only the supplied capability metadata.",
                "Ground the read-only export plan in the provided capability summary.",
                "Mention required credentials without requesting secret values.",
                "PyProcore MCP discovery itself performs no live calls.",
            ],
            ["capability_summary", "resource_goal"],
        ),
        _prompt(
            "plugin_developer_prompt",
            "Plugin Developer Prompt",
            "Help design metadata-only plugin manifests.",
            McpPromptKind.PLUGIN_DEVELOPER,
            [
                "Use only the supplied plugin metadata.",
                "Ground plugin guidance in metadata-only local evidence.",
                "Never request secrets, tokens, or credential files.",
                "PyProcore MCP does not execute plugins.",
            ],
            ["plugin_goal", "plugin_manifest_json"],
        ),
        _prompt(
            "eval_report_review_prompt",
            "Eval Report Review Prompt",
            "Review a local deterministic eval report.",
            McpPromptKind.EVAL_REPORT_REVIEW,
            [
                "Use only the supplied local eval report.",
                "Summarize failures, warnings, and cite evidence labels.",
                "Do not infer live Procore behavior from local fixtures.",
                "PyProcore MCP does not call models or Procore.",
            ],
            ["eval_report_json"],
        ),
        _prompt(
            "safety_boundary_review_prompt",
            "Safety Boundary Review Prompt",
            "Check saved output against PyProcore safety boundaries.",
            McpPromptKind.SAFETY_BOUNDARY_REVIEW,
            [
                "Use only supplied text and declared safety boundaries.",
                "Identify unsupported action language and missing grounding.",
                "Cite the exact local evidence label when available.",
                "PyProcore MCP is discovery-only unless a future guarded mode is enabled.",
            ],
            ["candidate_response", "safety_policy_json"],
        ),
    ]
    return sorted(prompts, key=lambda prompt: prompt.name)


def get_mcp_prompt(name: str) -> McpPrompt:
    """Return one MCP prompt template by name.

    Args:
        name: Prompt template name.

    Raises:
        KeyError: If the prompt is unknown.

    Returns:
        Prompt metadata and template text.
    """
    prompts = {prompt.name: prompt for prompt in list_mcp_prompts()}
    if name not in prompts:
        raise KeyError(f"MCP prompt is not registered: {name}")
    return prompts[name]


def safe_mcp_prompt_not_found(name: str) -> dict[str, object]:
    """Return a safe JSON-serializable response for an unknown prompt."""
    return {
        "isError": True,
        "error": "prompt_not_found",
        "name": name,
        "message": f"MCP prompt is not registered: {name}",
        "safety": _safety().model_dump(mode="json"),
    }


def _prompt(
    name: str,
    title: str,
    description: str,
    kind: McpPromptKind,
    lines: list[str],
    argument_names: list[str],
) -> McpPrompt:
    return McpPrompt(
        name=name,
        title=title,
        description=description,
        kind=kind,
        template="\n".join(f"- {line}" for line in lines),
        arguments=[
            McpPromptArgument(
                name=argument_name,
                description=f"Local placeholder input named {argument_name}.",
                required=True,
            )
            for argument_name in argument_names
        ],
        tags=[kind.value, "phase15a", "discovery_only"],
        safety=_safety(),
    )


def _safety() -> McpSafetyBoundary:
    return McpSafetyBoundary(
        notes=[
            "Prompt templates are local text metadata only.",
            "No model call, Procore call, plugin execution, or tool execution is performed.",
            "Prompts require grounding and limitation disclosure.",
        ]
    )
