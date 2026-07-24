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

## Scan A Local Codebase

Phase 18B can inspect a user-selected local folder for PyProcore imports,
object-client calls, helper calls, CLI references, and package references:

```bash
procore-sdk maintenance usage-scan \
  examples/maintenance/customer_codebase \
  --format markdown
```

The scanner uses Python AST parsing and bounded lexical checks. It skips common
virtual environment, build, cache, export, download, and secret directories,
does not follow directory symlinks, limits file size, rejects binary content,
and redacts common secret-looking snippet values before storing them.

## Build A Usage Map

```bash
procore-sdk maintenance usage-map \
  examples/maintenance/customer_codebase \
  --format json
```

The map groups detected usage into broad capability families such as RFIs,
submittals, workflows, analytics, catalog, and maintenance. Dynamic or
unresolved access is reported as unknown rather than guessed.

## Analyze Possible API Impact

Scan without OAS comparison data:

```bash
procore-sdk maintenance impact-scan \
  examples/maintenance/customer_codebase
```

Compare the same usage with two user-provided local OAS files:

```bash
procore-sdk maintenance impact-scan \
  examples/maintenance/customer_codebase \
  --old-oas examples/maintenance/old_fake_procore_oas.json \
  --new-oas examples/maintenance/new_fake_procore_oas.json \
  --format markdown
```

Impact labels are conservative: likely affected, possibly affected, unknown,
not affected, or deprecated/risky usage. They are broad review signals, not
proof of compatibility, production safety, or required migration.

The scanner never clones repositories, fetches remote code or OAS files,
executes or imports scanned files, edits customer code, generates patches,
commits, branches, or pull requests, calls Procore or external AI/model APIs,
or enables MCP, tool execution, or write actions.

## Build A Migration Patch Plan

Phase 18C turns local usage and possible-impact findings into conservative
human-review suggestions:

```bash
procore-sdk maintenance migration-plan \
  examples/maintenance/customer_codebase \
  --format markdown

procore-sdk maintenance patch-plan \
  examples/maintenance/customer_codebase \
  --old-oas examples/maintenance/old_fake_procore_oas.json \
  --new-oas examples/maintenance/new_fake_procore_oas.json \
  --format markdown
```

Suggestions distinguish removed endpoint review, changed parameters, newly
optional parameters, dynamic usage, CLI documentation, imports, local
analytics, and cases where no action is indicated. Dynamic, ambiguous, and
Python code usage remains manual-review only. Suggested unified diffs are
limited to static non-Python CLI/documentation references and are never applied.

## Write Optional Review Artifacts

Preview the fixed artifact set without writing:

```bash
procore-sdk maintenance patch-artifacts \
  examples/maintenance/customer_codebase \
  --old-oas examples/maintenance/old_fake_procore_oas.json \
  --new-oas examples/maintenance/new_fake_procore_oas.json \
  --output-dir ./tmp/migration-review \
  --dry-run
```

Without `--dry-run`, the command can write `migration_report.md`,
`migration_report.json`, `suggested_changes.diff`, `impacted_files.json`, and
`manual_review_checklist.md` beneath the selected output directory. Existing
artifacts are preserved unless `--overwrite` is explicit.

The artifact writer never touches scanned customer files, applies a patch,
runs git, stages or commits changes, creates a branch or pull request, fetches
remote code/OAS files, calls Procore or external AI/model APIs, or enables MCP,
tool execution, or write actions.

## Build A Local PR Draft Pack

Phase 18D converts the same local migration plan into human-review pull-request
draft materials:

```bash
procore-sdk maintenance pr-draft \
  examples/maintenance/customer_codebase \
  --format markdown

procore-sdk maintenance pr-draft-pack \
  examples/maintenance/customer_codebase \
  --old-oas examples/maintenance/old_fake_procore_oas.json \
  --new-oas examples/maintenance/new_fake_procore_oas.json \
  --output-dir ./tmp/pr-draft \
  --dry-run
```

The fixed artifact set contains `title.txt`, `body.md`,
`review_checklist.md`, `test_plan.md`, `risk_summary.md`,
`impacted_files.json`, `suggested_changes.diff`, `migration_report.md`, and
`metadata.json`. Dry-run is non-writing. Explicit local output preserves
existing files unless `--overwrite` is provided.

This is not PR automation. It does not edit customer files, apply patches, run
git, stage or commit files, call GitHub APIs, open pull requests, fetch remote
code or OAS files, call Procore or external AI/model APIs, or enable MCP/tool
or write execution. Every artifact requires human review.

## Human Review Checklist

1. Verify the endpoint in official Procore documentation.
2. Confirm company/project context and required headers.
3. Confirm pagination, filters, permissions, and response payloads.
4. Replace flexible draft fields with reviewed typed models.
5. Add mocked success, error, pagination, and authorization tests.
6. Update API coverage, CLI, examples, and changelog documentation.
7. Run the complete project quality suite.
8. Review Phase 18B impact labels against tests and official documentation.
9. Treat all Phase 18C diffs as suggestions and apply accepted changes manually.
10. Treat Phase 18D titles, bodies, checklists, and test plans as local drafts;
    create any real pull request manually after review.
