# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project follows semantic versioning.

## [Unreleased]

### Added

- Open-source repository support files, including contribution, security, issue, and pull request guidance.

## [2.0.0] - 2026-07-03

### Added

- Search and resolver layer for human-friendly project, company, RFI, and submittal lookup.
- Automation layer for packaging resolved Procore items for downstream workflows.
- `WorkflowPackage` model for metadata, raw payloads, and downloaded attachment references.
- `package-rfi` and `package-submittal` CLI commands.
- `find-company`, `find-project`, `find-rfi`, and `find-submittal` CLI commands.
- Expanded test suite to 114 tests with 96% coverage.

## [1.0.2] - 2026-07-03

### Changed

- Cleaned up PyPI metadata and license information.

## [1.0.1] - 2026-07-03

### Changed

- Restructured the project into a proper `pyprocore` package.
- Added `import pyprocore` support.
- Added `__version__` support.
- Added the installed `procore-sdk` CLI entry point.

## [1.0.0] - 2026-07-03

### Added

- Initial public release.
- OAuth authorization-code flow.
- Automatic token refresh.
- Company, project, RFI, and submittal services.
- Attachment download support.
- Typed Pydantic models.
- Command-line interface.
- Structured logging.
- Mocked unit tests.
