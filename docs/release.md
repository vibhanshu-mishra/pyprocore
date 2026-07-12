# Release Guide

This guide describes the local release-readiness process for PyProcore. It does
not publish to PyPI or create GitHub releases.

PyProcore `2.1.0` has been published to PyPI, verified from a clean virtual
environment, tagged as `v2.1.0`, and released on GitHub.

The repository source is now prepared for `2.2.0`, which includes the completed
Phase 7 agent-layer infrastructure. `2.2.0` has not been published to PyPI yet.

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

For the public release status summary, see [Project Status](project-status.md).

## Release Checklist

Before publishing a future release:

- Confirm no `.env`, token store, downloads, logs, or generated workflow outputs
  are tracked.
- Confirm the prepared version in both `pyproject.toml` and
  `pyprocore/__init__.py`.
- Confirm `CHANGELOG.md` has clear entries for the release.
- Confirm `README.md` installation, authentication, examples, and security
  notes are current.
- Confirm `pyproject.toml` metadata, dependencies, classifiers, and project URLs
  are accurate.
- Confirm package imports and CLI imports work locally.

## Release Candidate Validation

Before publishing `2.2.0` or any future release to TestPyPI or PyPI, build and inspect
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

For the prepared `2.2.0` release, use this order when the project is ready:

1. Run the docs truth audit.
2. Run release-candidate validation.
3. Upload to TestPyPI first.
4. Install from TestPyPI in a fresh virtual environment.
5. Run `procore-sdk --help`, `procore-sdk --version`, and import `pyprocore`.
6. Publish to PyPI only after the TestPyPI check succeeds.
7. Create the Git tag.
8. Create the GitHub release.
9. Perform post-release documentation cleanup.

Do not upload real `.env` files, OAuth token stores, logs, downloads, workflow
runs, webhook event stores, or generated AI/export folders.

## 2.1.0 Release Completed

The `2.1.0` release has already been completed. Do not publish it again.

To verify the published package:

```bash
python3 -m pip install pyprocore==2.1.0
procore-sdk --version
```

Expected output:

```text
pyprocore 2.1.0
```

For future releases, repeat the full validation flow, upload to TestPyPI first,
verify a clean install, publish to real PyPI only after final confirmation, then
create the Git tag and GitHub release.

## 2.2.0 Release Prepared

The `2.2.0` release is prepared in source but has not been published. Do not
claim it is available on PyPI until the TestPyPI, PyPI, tag, and GitHub release
steps are completed.

To verify the prepared source locally:

```bash
PYTHONPATH=. procore-sdk --version
python3 scripts/audit_docs_truth.py
make release-candidate-check
```

Expected local source version:

```text
pyprocore 2.2.0
```

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
