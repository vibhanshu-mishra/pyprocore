# Plugin Architecture

Phase 11A added safe plugin architecture foundations in the current stable
`v2.2.0` release. Phase 11B extends that foundation with safe local plugin hook
metadata and explicit in-process hook registration as unreleased branch work.

## What This Does

Plugins are described by local JSON-serializable manifests. A manifest can say
that a future extension may provide a workflow, exporter, validator, formatter,
report, integration adapter, agent metadata, or MCP metadata.

Phase 11A does not install plugins, fetch remote registries, import arbitrary
modules, or execute plugin code.

Phase 11B adds explicit local extension hooks. Hooks can run only when trusted
application code registers a Python callable in-process. Hook metadata in a
manifest is descriptive by itself and never executes code.

## Safety Boundaries

- No remote plugin installation.
- No internet or package-registry calls.
- No dynamic imports from plugin paths.
- No plugin code execution.
- No automatic hook execution from manifests.
- No arbitrary hook loading or string-based imports.
- No Procore create, update, delete, upload, approve, reject, submit, payment,
  or write actions.
- No live Procore API calls.
- No external AI/model calls.
- Agent tool execution remains disabled.
- MCP remains discovery-only.

## CLI Commands

```bash
procore-sdk plugins list
procore-sdk plugins show csv_exporter_plugin
procore-sdk plugins manifest --json
procore-sdk plugins sample-manifest --json
procore-sdk plugins validate ./plugin-manifest.json
procore-sdk plugins hooks
procore-sdk plugins hooks --type validator
procore-sdk plugins hook-manifest --json
procore-sdk plugins sample-hook-manifest --json
procore-sdk plugins run-sample-validator
procore-sdk plugins run-sample-formatter
```

These commands only inspect or validate plugin metadata. They do not require
Procore credentials.

The two sample run commands use built-in deterministic sample data and built-in
hooks only. They do not accept import paths, plugin packages, or user-provided
code.

## Manifest Shape

```json
{
  "schema_version": "1",
  "name": "example_exporter_plugin",
  "version": "1.0.0",
  "description": "Placeholder metadata for a future local exporter plugin.",
  "author": "Your Name",
  "homepage": "https://example.com/pyprocore-plugin",
  "capabilities": ["exporter", "formatter"],
  "requires_pyprocore": ">=2.2.0",
  "entry_points": {
    "exporter": "example_package.exporters"
  },
  "tags": ["example", "metadata-only"],
  "safety_level": "metadata_only",
  "enabled_by_default": false,
  "supports_sync": true,
  "supports_async": false,
  "supports_agent_metadata": false,
  "supports_cli": true,
  "hooks": [
    {
      "hook_name": "example_quality_validator",
      "plugin_name": "example_hook_plugin",
      "hook_type": "validator",
      "description": "Example local validator hook metadata.",
      "input_kind": "records",
      "output_kind": "validation_report",
      "supports_sync": true,
      "supports_async": false,
      "safe_by_default": true,
      "read_only": true,
      "notes": ["Metadata only. Explicit registration is required to run."]
    }
  ],
  "notes": [
    "Phase 11A validates this metadata only.",
    "No plugin code is installed, imported, or executed."
  ]
}
```

## Built-In Metadata Examples

PyProcore includes built-in metadata examples for future extension types:

- CSV exporter metadata
- JSONL exporter metadata
- Async batch metadata
- AI workflow prompt-pack metadata
- Enterprise readiness metadata

These built-ins describe possible extension categories. They do not change SDK
runtime behavior.

## Safe Local Extension Hooks

Phase 11B introduces controlled local hook types:

- `validator`
- `exporter`
- `formatter`
- `report`
- `workflow_helper`
- `record_transformer`

Application code may explicitly register trusted callables:

```python
from pyprocore.plugins import PluginHookMetadata, PluginHookRegistry, PluginHookType

registry = PluginHookRegistry()
registry.register_hook(
    PluginHookMetadata(
        hook_name="local_quality_check",
        plugin_name="my_local_plugin",
        hook_type=PluginHookType.VALIDATOR,
        description="Validate local records.",
    ),
    lambda context, records: {"valid": True, "count": len(records)},
)
```

This is intentionally local and explicit. PyProcore does not discover hook code,
load modules by string, install packages, or fetch hook definitions from the
internet.

## Built-In Safe Hooks

PyProcore includes deterministic local hooks for examples and lightweight
automation:

- `validate_required_fields`
- `validate_no_empty_ids`
- `format_records_as_summary`
- `transform_records_select_fields`
- `export_records_to_jsonl_payload`
- `build_basic_quality_report`

These hooks operate on caller-provided local data. They do not call Procore,
write files, contact model APIs, or require credentials.

## Hook Contexts and Results

Hook contexts intentionally exclude raw access tokens, refresh tokens, client
secrets, Authorization headers, and live Procore clients by default. Hook
outputs and captured errors are sanitized before becoming `PluginHookResult`
objects.

Hook registry manifests contain hook metadata only. They are safe to serialize
for review:

```bash
procore-sdk plugins hook-manifest --json
```

## What Phase 11B Does Not Do

- It does not enable remote plugin installation.
- It does not fetch plugin registries.
- It does not import arbitrary plugin modules.
- It does not run code from manifest metadata.
- It does not add Procore write actions.
- It does not enable agent tool execution.
- It does not enable MCP execution.
- It does not call external AI/model APIs.

## Future Work

Future phases may add stricter signed or trusted plugin loading, but Phase 11B
stays local and explicit.
