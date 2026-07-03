# PyProcore

> A production-ready Python SDK for building automation, integrations, and AI workflows on top of the Procore REST API.

[![PyPI](https://img.shields.io/pypi/v/pyprocore.svg)](https://pypi.org/project/pyprocore/)
![Python](https://img.shields.io/badge/python-3.12%2B-blue.svg)
[![License](https://img.shields.io/pypi/l/pyprocore.svg)](LICENSE)
[![Tests](https://github.com/vibhanshu-mishra/pyprocore/actions/workflows/tests.yml/badge.svg)](https://github.com/vibhanshu-mishra/pyprocore/actions/workflows/tests.yml)
![Coverage](https://img.shields.io/badge/coverage-96%25-brightgreen.svg)

PyProcore handles the parts of a Procore integration that are tedious and easy to get wrong — OAuth, token refresh, pagination, retries, typed responses, structured logging, and attachment downloads — so you work with Python objects instead of raw JSON and API plumbing.

---

## Why PyProcore

Calling the Procore REST API directly means managing the OAuth handshake, refreshing expired tokens, following pagination headers, retrying failed requests, and parsing untyped JSON on every call.

PyProcore does that once, correctly, behind a clean interface. You call a service method and get back a typed Pydantic object. It is designed as the foundation layer for higher-level tools built on Procore data: engineering assistants, document analysis, workflow automation, and AI-powered review.

---

## Features

**Authentication and transport**

- OAuth 2.0 authorization-code flow
- Automatic access-token refresh
- Automatic pagination via Procore response headers
- Request retries and structured logging with secret redaction

**API coverage**

- Companies
- Projects
- RFIs
- Submittals
- Attachment downloads

**Developer experience**

- Typed Pydantic response models
- Command-line interface
- 114 unit tests at 96% coverage, mocked with no live Procore dependency

---

## Architecture

| Package               | Responsibility                                                  |
| --------------------- | --------------------------------------------------------------- |
| `pyprocore/auth/`     | OAuth exchange, token persistence, token refresh                |
| `pyprocore/core/`     | Configuration, endpoint paths, HTTP client, logging, exceptions |
| `pyprocore/models/`   | Pydantic response models                                        |
| `pyprocore/services/` | Company, project, RFI, submittal, and file services             |
| `pyprocore/parser/`   | Email parsing utilities for future automation                   |
| `tests/`              | Mocked unit tests with no live Procore dependency               |

---

## Installation

Requires Python 3.12+.

```bash
pip3 install pyprocore
```

For local development:

```bash
git clone https://github.com/vibhanshu-mishra/pyprocore.git
cd pyprocore
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -e .
```

---

## Quick Example

```python
from pyprocore.services import list_projects

projects = list_projects(company_id=123456)

for project in projects:
    print(project.name)
```

---

## Configuration

Copy the example file and fill in real values:

```bash
cp .env.example .env
```

Required variables:

```bash
PROCORE_CLIENT_ID=your_client_id
PROCORE_CLIENT_SECRET=your_client_secret
PROCORE_REDIRECT_URI=http://localhost:8080/callback
PROCORE_LOGIN_URL=https://login.procore.com
PROCORE_API_BASE=https://api.procore.com
PROCORE_COMPANY_ID=123456
```

Secrets, tokens, URLs, and company IDs are never hardcoded in source.

---

## Authentication

Exchange the first authorization code and save the token locally:

```python
from pyprocore.auth.oauth import exchange_authorization_code
from pyprocore.auth.token_manager import TokenManager

token_response = exchange_authorization_code("authorization-code-from-procore")
TokenManager().save_oauth_response(token_response)
```

After that, SDK clients read the token automatically:

```python
from pyprocore.auth.token_manager import get_access_token

access_token = get_access_token()
```

Expired access tokens refresh automatically whenever a refresh token is available.

---

## Usage

Once `.env` is configured and the one-time OAuth exchange is complete, calls return typed objects:

```python
from pyprocore.services import list_projects

for project in list_projects(company_id=123456):
    print(project.name)
```

Full service surface:

```python
from pyprocore.services import (
    download_rfi_attachments,
    download_submittal_attachments,
    get_rfi,
    get_submittal,
    list_companies,
    list_projects,
    list_rfis,
    list_submittals,
)

companies = list_companies()
projects = list_projects(company_id=123456)

rfis = list_rfis(project_id=352338)
rfi = get_rfi(project_id=352338, rfi_id=102784)
first_attachment_url = rfi.questions[0].attachments[0].url

submittals = list_submittals(project_id=352338)
submittal = get_submittal(project_id=352338, submittal_id=309641)
```

Human-friendly resolvers are available when you do not already know Procore IDs:

```python
from pyprocore import find_company, find_project, find_rfi, find_submittal
from pyprocore.services import find_project_contains

company = find_company("Tracker")
project = find_project("Sandbox Test Project")
project_by_number = find_project(number="001")
hospital_project = find_project_contains("Hospital")

rfi = find_rfi(project_id=352338, number="15")
submittal = find_submittal(project_id=352338, number="27")
```

Resolvers use case-insensitive exact matching first, then partial matching. They raise `NotFoundError`, `DuplicateMatchError`, or `MultipleResultsError` when a lookup cannot produce exactly one typed result.

## Automation Layer

The automation layer builds a single typed package for downstream workflows. It resolves project and item identifiers, fetches full metadata, optionally downloads attachments, and returns one JSON-serializable `WorkflowPackage`.

```python
from pyprocore.automation import AutomationInput, build_workflow_package

package = build_workflow_package(
    AutomationInput(
        project_name="Sandbox Test Project",
        item_type="rfi",
        item_number="15",
    )
)

print(package.title)
print(package.attachments)
```

Convenience builders are available when you already know the workflow type:

```python
from pyprocore.automation import build_rfi_package, build_submittal_package

rfi_package = build_rfi_package(project_id=352338, rfi_id=102784)
submittal_package = build_submittal_package(
    project_name="Sandbox Test Project",
    number="27",
    download_attachments=False,
)
```

Default attachment output directories are created under `downloads/`, for example `downloads/rfi_15/` or `downloads/submittal_27/`. Pass `output_dir` to choose a custom destination.

Every typed model serializes back to JSON:

```python
json_payload = rfi.model_dump(mode="json")
json_string = rfi.model_dump_json()
```

---

## Downloading Attachments

Attachment URLs live at:

```text
RFI:        questions[].attachments[].url
Submittal:  attachments[].url
```

Download through the service functions:

```python
rfi_files = download_rfi_attachments(project_id=352338, rfi_id=102784)
submittal_files = download_submittal_attachments(
    project_id=352338,
    submittal_id=309641,
)
```

The shared file service supports safe filenames, streaming writes, retries, progress logging, batch downloads, and skip-existing behavior by default:

```python
from pyprocore.services.files import FileDownloadService

files = FileDownloadService().download_attachments(
    attachments,
    "downloads/custom",
    fallback_prefix="attachment",
    overwrite=False,
)
```

---

## CLI

```bash
procore-sdk companies
procore-sdk find-company Tracker
procore-sdk projects
procore-sdk find-project Hospital
procore-sdk find-project --number 001
procore-sdk rfis --project 352338
procore-sdk rfi --project 352338 --id 102784
procore-sdk find-rfi --project 352338 --number 15
procore-sdk submittals --project 352338
procore-sdk submittal --project 352338 --id 309641
procore-sdk find-submittal --project 352338 --number 27
procore-sdk download-rfi --project 352338 --id 102784
procore-sdk download-submittal --project 352338 --id 309641
procore-sdk package-rfi --project 352338 --id 102784
procore-sdk package-rfi --project-name "Sandbox Test Project" --number 15
procore-sdk package-submittal --project 352338 --id 309641
procore-sdk package-submittal --project-name "Sandbox Test Project" --number 27
```

The CLI prints formatted JSON. Typed models are serialized with `model_dump(mode="json")`.

---

## Pagination

Collection methods use `ProcoreClient.get_all()`, which follows Procore pagination headers automatically. Business logic should call the service method or `get_all()` directly and never request page 2 by hand.

---

## Logging

Structured logs are written to:

```text
logs/sdk.log
logs/errors.log
```

Request logs record method, endpoint, status, elapsed time, and retry count. Exception logs record stack traces, exception type, request URL, HTTP status, and response body when available. The logger redacts sensitive keys such as authorization headers, access tokens, refresh tokens, and client secrets.

---

## Implemented Endpoints

```text
GET /rest/v1.0/companies
GET /rest/v1.0/companies/{company_id}/projects
GET /rest/v1.1/projects/{project_id}/rfis
GET /rest/v1.1/projects/{project_id}/rfis/{rfi_id}
GET /rest/v1.1/projects/{project_id}/submittals
GET /rest/v1.1/projects/{project_id}/submittals/{submittal_id}
```

---

## Roadmap

**Planned endpoints**

- Drawings
- Documents
- Specifications
- Daily Logs
- Photos
- Correspondence
- Observations

**Planned capabilities**

- AI workflow examples built on the SDK

---

## Troubleshooting

| Error                       | Likely cause and fix                                                                                           |
| --------------------------- | -------------------------------------------------------------------------------------------------------------- |
| `ConfigurationError`        | `.env` is missing or a required key is absent.                                                                 |
| `AuthenticationError`       | Complete the first OAuth code exchange; confirm `pyprocore/auth/token_store.json` holds a refresh token.       |
| `AuthorizationError`        | The Procore user lacks access to the target company, project, or resource.                                     |
| `ResourceNotFoundError`     | Project, RFI, or submittal ID is wrong for the configured company.                                             |
| Attachments not downloading | Check `logs/errors.log` for HTTP status and response body. Existing files are skipped unless `overwrite=True`. |

---

## Tests

Run unit tests:

```bash
.venv/bin/python -m unittest discover -s tests
```

Run coverage:

```bash
.venv/bin/python -m coverage run -m unittest discover -s tests
.venv/bin/python -m coverage report
```

---

## Development

Clone the repository and install the package in editable mode:

```bash
git clone https://github.com/vibhanshu-mishra/pyprocore.git
cd pyprocore

python3 -m venv .venv
source .venv/bin/activate

pip install -e ".[dev]"
```

If you're working in a restricted environment where build isolation cannot access PyPI, install with:

```bash
pip install --no-build-isolation -e ".[dev]"
```

Useful development commands:

```bash
make lint
make typecheck
make test
make coverage
```

---

## Project Resources

- [Changelog](CHANGELOG.md)
- [Contributing](CONTRIBUTING.md)
- [Security](SECURITY.md)
- [Code of Conduct](CODE_OF_CONDUCT.md)
- [Architecture notes](docs/architecture.md)
- [Roadmap](docs/roadmap.md)

---

## Supported Environments

- Procore Production
- Procore Sandbox

---

## Contributing

Contributions, issues, and feature requests are welcome. Please open an issue before submitting large changes.

---

## License

Released under the MIT License. See [LICENSE](LICENSE) for details.

---

> **Disclaimer** — PyProcore is an independent open-source project and is not affiliated with or endorsed by Procore Technologies.
