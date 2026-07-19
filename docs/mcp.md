# MCP Discovery

Phase 15A and Phase 15B add richer MCP discovery metadata for PyProcore. This
is unreleased branch work after the published `2.2.0` release.

MCP support remains discovery-only. It does not call Procore, call external
AI/model APIs, execute plugins, execute tools, fetch remote MCP resources, or
perform uploads, writes, approvals, submissions, status changes, payments, or
other mutations.

## What MCP Exposes

- Local resource metadata for agent manifests, tool schemas, OpenAPI, eval
  suites, baseline/regression/history templates, model-response fixtures,
  plugin metadata, async capabilities, async export and batch patterns, AI
  workflow templates, safety boundaries, and docs references.
- Prompt templates for RFI review, submittal review, project context Q&A,
  drawing/spec comparison, engineering assistant support, field issue summaries,
  change-risk review, async export planning, plugin development, eval and
  regression review, model fixture review, plugin config review, async batch
  review, AI workflow package review, MCP safety review, and release readiness
  review.
- Capability summaries that clearly mark execution as disabled.
- Stdio-friendly JSON discovery payloads for local MCP client experiments.
- Optional resource and prompt kind filters for local inspection.

## CLI Commands

```bash
procore-sdk mcp manifest
procore-sdk mcp resources
procore-sdk mcp resources --kind eval_suite
procore-sdk mcp resource pyprocore://agent/manifest
procore-sdk mcp prompts
procore-sdk mcp prompts --kind eval_report_review
procore-sdk mcp prompt rfi_review_prompt
procore-sdk mcp capabilities
procore-sdk mcp safety
procore-sdk mcp stdio-discovery
```

Use `--pretty` for formatted JSON and `--output PATH` on list/manifest-style
commands when you want to save local metadata.

## Python Usage

```python
from pyprocore.mcp import (
    build_mcp_capability_summary,
    build_mcp_discovery_manifest,
    list_mcp_prompts,
    list_mcp_resources,
)

manifest = build_mcp_discovery_manifest()
resources = list_mcp_resources()
eval_resources = list_mcp_resources(kind="eval_suite")
prompts = list_mcp_prompts()
review_prompts = list_mcp_prompts(kind="eval_report_review")
summary = build_mcp_capability_summary()

print(manifest.server.name)
print(len(resources), len(prompts))
print(len(eval_resources), len(review_prompts))
print(summary.safety.mcp_execution_enabled)
```

## Safety Boundary

MCP discovery is safe to run without credentials because it uses local metadata
only. Unknown resources and prompts return safe not-found responses. Tool-call
requests still return disabled execution responses.

Future phases may explore guarded execution, but Phase 15A and 15B do not
enable it.
