# Release Guide

This guide describes the local release-readiness process for PyProcore. It does
not publish to PyPI or create GitHub releases.

## Versioning

PyProcore follows SemVer:

- Patch versions for bug fixes and documentation-only package polish.
- Minor versions for additive SDK features.
- Major versions for breaking public API changes.

Keep `pyproject.toml`, `pyprocore/__init__.py`, and `CHANGELOG.md` aligned when
a release intentionally changes the package version.

## Pre-release Checklist

Run:

```bash
python3 scripts/check_release_ready.py
make examples-check
make test
make coverage
make lint
make typecheck
python3 -m black --check .
python3 -m isort --check-only .
```

Or run the combined target:

```bash
make release-check
```

For the final repository-level readiness summary, see
[Final Release Readiness](final-release-readiness.md).

## Release Checklist

Before publishing:

- Confirm no `.env`, token store, downloads, logs, or generated workflow outputs
  are tracked.
- Confirm `CHANGELOG.md` has clear entries for the release.
- Confirm `README.md` installation, authentication, examples, and security
  notes are current.
- Confirm `pyproject.toml` metadata, dependencies, classifiers, and project URLs
  are accurate.
- Confirm package imports and CLI imports work locally.

## Release Candidate Validation

Before publishing to TestPyPI or PyPI, build and inspect release artifacts
locally:

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
- Verifies `import pyprocore`, important public exports, and
  `procore-sdk --help`.

If `twine` is not installed, the checker warns by default. Use strict mode when
you want missing optional release tooling to fail the check:

```bash
python3 scripts/check_release_candidate.py --strict
```

To inspect the generated artifacts manually, keep them after validation:

```bash
python3 scripts/check_release_candidate.py --keep-artifacts
ls dist/
```

Do not commit `dist/`, `build/`, `*.egg-info/`, temporary virtual
environments, credentials, token stores, logs, downloads, or generated workflow
outputs. The release-candidate check does not publish anything and does not
create a GitHub release.

## PyPI Publishing Checklist

Publishing is intentionally manual for now. Running the release checks does not
publish to PyPI and does not create a GitHub release.

When the project is ready:

1. Build the source distribution and wheel in a clean environment.
2. Inspect the artifacts to make sure secrets and generated outputs are absent.
3. Upload to TestPyPI first.
4. Install from TestPyPI in a fresh virtual environment.
5. Run `procore-sdk --help` and import `pyprocore`.
6. Publish to PyPI only after the TestPyPI check succeeds.

Do not upload real `.env` files, OAuth token stores, logs, downloads, workflow
runs, webhook event stores, or generated AI/export folders.

## Changelog Updates

Keep an `[Unreleased]` section at the top of `CHANGELOG.md`.

Group entries under:

- `Added`
- `Changed`
- `Fixed`
- `Docs`
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
