# Release Guide

This guide describes PyProcore's release-readiness process. Release checks are
local by default; they do not publish to PyPI and do not create GitHub releases.

## Current Release

PyProcore `2.2.0` has been published to PyPI, verified from a clean install,
tagged as `v2.2.0`, and released on GitHub.

PyProcore `2.1.0` is the previous stable release.

## Verify 2.2.0

To verify the published package in a clean environment:

```bash
python3 -m pip install pyprocore==2.2.0
procore-sdk --version
procore-sdk agent tools
procore-sdk agent evals run
```

Expected version output:

```text
pyprocore 2.2.0
```

The agent commands above inspect local metadata and deterministic evals. They do
not execute Procore tools, call live Procore APIs, or call external AI/model
APIs.

## Versioning

PyProcore follows SemVer:

- Patch versions for bug fixes and documentation-only package polish.
- Minor versions for additive SDK features.
- Major versions for breaking public API changes.

Keep `pyproject.toml`, `pyprocore/__init__.py`, and `CHANGELOG.md` aligned when
a release intentionally changes the package version.

## Pre-release Checklist For Future Releases

Run:

```bash
python3 scripts/audit_docs_truth.py
python3 scripts/check_release_ready.py
python3 scripts/check_secrets.py
make examples-check
make test
make coverage
make lint
make typecheck
python3 -m black --check .
python3 -m isort --check-only .
make docs-build
```

Or run the combined target:

```bash
make quality-check
```

For a package-oriented release-readiness subset, run:

```bash
make release-check
```

For the public release status summary, see [Project Status](project-status.md).

## Release Candidate Validation

Before publishing a future release to TestPyPI or PyPI, build and inspect
release artifacts locally:

```bash
python3 -m pip install build twine
make release-candidate-check
```

The release-candidate checker:

- Removes stale local `dist/`, `build/`, and `*.egg-info/` artifacts.
- Builds the source distribution and wheel with `python3 -m build`.
- Falls back to `python3 -m build --no-isolation` with a warning when an
  offline environment cannot fetch isolated build dependencies.
- Verifies that both `.tar.gz` and `.whl` artifacts exist.
- Inspects package metadata such as name, version, summary, Python requirement,
  license metadata, and dependencies.
- Runs `twine check` when `twine` is installed.
- Installs the built wheel into a clean temporary virtual environment.
- Falls back to a local-dependency install check with a warning when an offline
  environment cannot resolve runtime dependencies.
- Verifies `import pyprocore`, important public exports, and `procore-sdk --help`.

The release-candidate check does not publish anything.

If `twine` is not installed, the checker warns by default. Use strict mode when
you want missing optional release tooling to fail the check:

```bash
python3 scripts/check_release_candidate.py --strict
```

Do not commit `dist/`, `build/`, `*.egg-info/`, temporary virtual environments,
credentials, token stores, logs, downloads, or generated workflow outputs.

## Publishing Checklist For Future Releases

Publishing is intentionally manual. Running release checks does not publish to
PyPI and does not create a GitHub release.

For future releases, use this order:

1. Run the docs truth audit.
2. Run release-candidate validation.
3. Upload to TestPyPI first.
4. Install from TestPyPI in a fresh virtual environment.
5. Run `procore-sdk --help`, `procore-sdk --version`, and import `pyprocore`.
6. Publish to real PyPI only after the TestPyPI check succeeds.
7. Create the Git tag.
8. Create the GitHub release.
9. Perform post-release documentation cleanup.

Do not upload real `.env` files, OAuth token stores, logs, downloads, workflow
runs, webhook event stores, or generated AI/export folders.

## 2.2.0 Release Completed

The `2.2.0` release has already been completed. Do not publish it again and do
not create another `v2.2.0` GitHub release.

Completed release steps:

- PyPI release completed.
- PyPI publication completed.
- Clean install verification completed.
- CLI version check completed.
- Phase 7 local agent metadata/eval commands verified.
- Git tag `v2.2.0` created.
- GitHub release created.
- Post-release documentation cleanup completed.

## Changelog Updates

Keep an `[Unreleased]` section at the top of `CHANGELOG.md`.

Group entries under:

- `Added`
- `Changed`
- `Fixed`
- `Docs`
- `Security`
- `Tests`

When cutting a release, move relevant unreleased entries under the new version
heading and start a fresh `[Unreleased]` section.

## Local Release Check

The release checker is local-only:

```bash
python3 scripts/check_release_ready.py
```

It checks required files, package metadata, package imports, CLI imports,
documentation folders, example folders, and obvious tracked secret files. It
prints `PASS`, `WARN`, and `FAIL` lines and exits nonzero only for serious
release-readiness failures.
