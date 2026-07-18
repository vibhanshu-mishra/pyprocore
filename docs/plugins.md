# Plugin Architecture

Phase 11A adds a safe plugin architecture foundation for PyProcore as
unreleased branch work. It is intentionally metadata-first.

## What This Does

Plugins are described by local JSON-serializable manifests. A manifest can say
that a future extension may provide a workflow, exporter, validator, formatter,
report, integration adapter, agent metadata, or MCP metadata.

Phase 11A does not install plugins, fetch remote registries, import arbitrary
modules, or execute plugin code.

## Safety Boundaries

- No remote plugin installation.
- No internet or package-registry calls.
- No dynamic imports from plugin paths.
- No plugin code execution.
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
```

These commands only inspect or validate plugin metadata. They do not require
Procore credentials.

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

## Future Work

Future phases may add controlled extension hooks. Any future execution path
should remain explicit, reviewed, and separate from Phase 11A metadata
discovery.
