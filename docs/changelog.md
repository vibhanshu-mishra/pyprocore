# Changelog

PyProcore follows semantic versioning and keeps release notes in a root-level
changelog. The changelog is the best place to review:

- changes collected for the next release
- published version history
- added, changed, fixed, docs, and test updates
- release-readiness notes

The canonical changelog lives in the GitHub repository:

- [CHANGELOG.md on GitHub](https://github.com/vibhanshu-mishra/pyprocore/blob/main/CHANGELOG.md)

Current release status:

- `2.4.0` is the latest published stable PyPI release.
- `2.3.0` is the previous stable release.
- `2.3.0` introduced expanded read coverage, enterprise hardening, async helpers,
  metadata-only plugins, AI workflow examples, deterministic evals, and
  discovery-only MCP compatibility tooling.
- The root changelog records the released `2.4.0` work: Phase 16A-16B,
  Phase 17A-17E, and Phase 18A-18F.
- Phase 18A adds local OAS drift, coverage-gap,
  maintenance-plan, and draft read-only scaffold assistance.
- Phase 18B adds local codebase usage maps,
  redacted snippets, and conservative possible-impact reports.
- Phase 18C adds local migration plans,
  documentation-only suggested diffs, review checklists, and optional
  patch-plan artifacts that are never applied automatically.
- Phase 18D adds local PR draft titles, body
  previews, review checklists, safe test plans, risk summaries, and optional
  artifacts. It does not run git, call GitHub, or open pull requests.
- Phase 18E adds local compatibility contract
  generation, validation, diffs, and codebase usage comparison. Contracts are
  metadata and do not certify production compatibility.
- Phase 18F adds local migration guides,
  deprecation summaries, upgrade/test checklists, and bounded report artifacts.
- `2.2.0` remains part of the historical release record.

Before cutting a release, update the changelog with concise user-facing notes and
run the local release checks described in the [Release Guide](release.md).
