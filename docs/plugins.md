# Plugin Architecture

Phase 11A added safe plugin architecture foundations in the current stable
`v2.2.0` release. Phase 11B, Phase 11C, and Phase 11D extend that foundation
as unreleased branch work with safe local hooks, JSON configuration,
extension-pack manifests, and plugin developer scaffolding.

## What This Does

Plugins are described by local JSON-serializable manifests. A manifest can say
that a future extension may provide a workflow, exporter, validator, formatter,
report, integration adapter, agent metadata, or MCP metadata.

Phase 11A does not install plugins, fetch remote registries, import arbitrary
modules, or execute plugin code.

Phase 11B adds explicit local extension hooks. Hooks can run only when trusted
application code registers a Python callable in-process. Hook metadata in a
manifest is descriptive by itself and never executes code.

Phase 11D adds local developer scaffolding for templates. A scaffold can create
placeholder JSON, Markdown, docs, example, and test files, but generated files
are not loaded, imported, installed, or executed by PyProcore.

Phase 13A adds local golden evals that can inspect plugin manifests, plugin
configuration, and extension-pack metadata. These evals are deterministic
checks only and do not execute plugin code.

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

## Plugin Configuration Files

Phase 11C adds safe JSON plugin configuration files as unreleased branch work.
These files store preferences only:

- enabled and disabled plugin metadata names
- enabled and disabled capability categories
- hook preference metadata
- local extension-pack names
- tags, notes, and a metadata-only safety policy

Example:

```json
{
  "config_version": "1",
  "enabled_plugins": ["csv_exporter_plugin"],
  "enabled_capabilities": ["exporter"],
  "hook_preferences": [
    {
      "hook_name": "validate_required_fields",
      "hook_type": "validator",
      "enabled": true
    }
  ],
  "safety_policy": "metadata_only"
}
```

Validate and summarize config locally:

```bash
procore-sdk plugins config sample --json
procore-sdk plugins config validate examples/configs/plugin_config_minimal.json
procore-sdk plugins config summary examples/configs/plugin_config_hooks.json
procore-sdk plugins config manifest examples/configs/plugin_config_enterprise.json
```

The config manifest command applies preferences to registered plugin metadata
only. It does not install, import, fetch, register, or execute plugin code.

## Local Extension-Pack Manifests

Extension packs are JSON metadata bundles. They can describe related plugin
manifests, hook metadata, capabilities, tags, and notes:

```json
{
  "schema_version": "1",
  "name": "starter_export_pack",
  "version": "1.0.0",
  "description": "Metadata-only bundle for local export helpers.",
  "included_plugins": [{"plugin_name": "csv_exporter_plugin"}],
  "included_hooks": [
    {
      "hook_name": "validate_required_fields",
      "plugin_name": "enterprise_readiness_plugin",
      "hook_type": "validator",
      "description": "Validate required local record fields."
    }
  ],
  "capabilities": ["exporter", "validator"],
  "safety_level": "metadata_only"
}
```

Inspect extension-pack metadata locally:

```bash
procore-sdk plugins extension-pack sample --json
procore-sdk plugins extension-pack validate examples/configs/plugin_extension_pack_sample.json
procore-sdk plugins extension-pack summary examples/configs/plugin_extension_pack_ai_workflows.json
```

Extension packs cannot execute hooks, register callables, import modules,
install packages, fetch remote resources, or call Procore.

## Plugin Developer Scaffolding

Phase 11D adds safe local scaffold helpers for developers who want starter
files for plugin metadata and documentation. Scaffolding is local template
generation only.

Available scaffold commands:

```bash
procore-sdk plugins scaffold sample-plan
procore-sdk plugins scaffold dry-run --name example_local_plugin --output-dir ./tmp-plugin
procore-sdk plugins scaffold create --name example_local_plugin --output-dir ./tmp-plugin
procore-sdk plugins scaffold extension-pack --name example_local_plugin --output-dir ./tmp-pack
procore-sdk plugins scaffold config --name example_local_plugin --output-dir ./tmp-config
procore-sdk plugins scaffold hook-pack --name example_local_plugin --output-dir ./tmp-hooks
```

`sample-plan` prints a safe example plan. `dry-run` renders the plan in memory
and writes nothing. `create` writes static files under the selected output
directory.

Generated full-pack files include:

- `README.md`
- `CHANGELOG.md`
- `plugin_manifest.json`
- `plugin_config.json`
- `extension_pack_manifest.json`
- `hook_manifest.json`
- `docs/plugin-pack.md`
- `examples/plugin_usage.py`
- `tests/test_plugin_manifest.py`

The Python files are static templates. PyProcore does not execute them during
scaffolding and does not auto-load them later.

### Output Path Safety

Scaffold requests reject remote-looking paths and path traversal. Template file
names must stay relative, and write mode verifies each target is inside the
selected output directory before writing.

### Overwrite Controls

Scaffolding skips existing files by default:

```bash
procore-sdk plugins scaffold create --name example_local_plugin --output-dir ./tmp-plugin
```

Use `--overwrite` only when you intentionally want to replace existing template
files:

```bash
procore-sdk plugins scaffold create --name example_local_plugin --output-dir ./tmp-plugin --overwrite
```

### What Phase 11D Does Not Do

- It does not install plugin packages.
- It does not fetch remote plugin resources.
- It does not auto-load plugins from arbitrary file paths.
- It does not dynamically import generated modules.
- It does not execute generated files.
- It does not execute hooks from configuration files.
- It does not call Procore or external AI/model APIs.
- It does not add Procore write, upload, approval, submission, or payment actions.
- It does not enable agent tool execution.
- MCP remains discovery-only.

## What Phase 11B Does Not Do

- It does not enable remote plugin installation.
- It does not fetch plugin registries.
- It does not import arbitrary plugin modules.
- It does not run code from manifest metadata.
- It does not add Procore write actions.
- It does not enable agent tool execution.
- It does not enable MCP execution.
- It does not call external AI/model APIs.

## What Phase 11C Does Not Do

- It does not support YAML or Python config files.
- It does not allow config files to point to executable Python code.
- It does not auto-load plugins from arbitrary paths.
- It does not install packages.
- It does not fetch remote plugin registries.
- It does not dynamically import modules.
- It does not execute hooks from config.
- It does not register callables from extension-pack manifests.
- It does not add Procore write actions.
- It does not enable agent tool execution.
- It does not enable MCP execution.
- It does not call external AI/model APIs.

## Future Work

Future phases may add stricter signed or trusted plugin packaging, but Phase
11B, Phase 11C, and Phase 11D stay local, explicit, and metadata-first.
