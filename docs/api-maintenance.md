# API Maintenance Assistant

Phase 18A adds a local, maintainer-oriented assistant for comparing
user-provided OpenAPI/OAS JSON files and planning safe read-only SDK coverage.
It helps maintainers review API drift; it does not automatically update
PyProcore.

## Safety Boundaries

The maintenance assistant:

- reads local JSON files only;
- never downloads or fetches an OAS document;
- never calls Procore or an external AI/model API;
- never generates executable tools or registers MCP capabilities;
- never implements or scaffolds write/mutation endpoints;
- never stages, commits, pushes, opens pull requests, or publishes packages;
- requires human review before any draft is integrated.

MCP remains discovery-only and Procore tool execution remains disabled.

## Compare Local OAS Files

```bash
procore-sdk maintenance drift \
  examples/maintenance/old_fake_procore_oas.json \
  examples/maintenance/new_fake_procore_oas.json \
  --format markdown
```

The report detects added and removed operations, changed method sets,
parameters, operation IDs, and changes classified as risky.

## Analyze Coverage Gaps

```bash
procore-sdk maintenance coverage-gaps \
  examples/maintenance/new_fake_procore_oas.json \
  --format json
```

Coverage comparison uses the existing PyProcore resource-area inventory. A
reported candidate is not proof that an exact endpoint is unsupported or safe
for production. Maintainers must verify official endpoint shape, context IDs,
permissions, pagination, and payloads.

## Build A Maintenance Plan

```bash
procore-sdk maintenance plan \
  examples/maintenance/new_fake_procore_oas.json \
  --format markdown
```

The plan groups endpoint metadata into safe read-only candidates,
endpoint-shape review, risky/write deferrals, documentation updates, and
suggested tests/examples.

## Plan A Draft Scaffold

```bash
procore-sdk maintenance scaffold-plan \
  examples/maintenance/new_fake_procore_oas.json \
  --path '/rest/v1.0/projects/{project_id}/readiness_checks' \
  --method GET
```

Scaffold plans contain clearly marked draft service, model, test, example, and
documentation strings. The draft service raises `NotImplementedError`; it is
not registered or production-ready.

## Dry-run Or Copy Draft Files

Dry-run validates destination paths without creating files:

```bash
procore-sdk maintenance scaffold-read-endpoint \
  examples/maintenance/new_fake_procore_oas.json \
  --path '/rest/v1.0/projects/{project_id}/readiness_checks' \
  --method GET \
  --output-dir ./tmp/api-maintenance-draft \
  --dry-run
```

Remove `--dry-run` only when you intentionally want draft files copied.
Existing files are preserved unless `--overwrite` is explicitly supplied.
Paths are constrained beneath the selected output directory.

POST, PATCH, PUT, and DELETE are refused. GET/HEAD/OPTIONS endpoints with risky
terms such as upload, approve, submit, payment, import, delete, close, or reopen
are also refused.

## Human Review Checklist

1. Verify the endpoint in official Procore documentation.
2. Confirm company/project context and required headers.
3. Confirm pagination, filters, permissions, and response payloads.
4. Replace flexible draft fields with reviewed typed models.
5. Add mocked success, error, pagination, and authorization tests.
6. Update API coverage, CLI, examples, and changelog documentation.
7. Run the complete project quality suite.
