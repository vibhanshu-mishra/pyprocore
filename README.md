# Procore SDK

Production-quality Python SDK and automation foundation for the Procore REST API.

The SDK handles configuration, OAuth token refresh, authenticated HTTP requests,
pagination, typed response models, structured logging, and attachment downloads
for companies, projects, RFIs, and submittals.

## Installation

Requires Python 3.12+.

```bash
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt
```

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

## Authentication

Exchange the first authorization code and save the token locally:

```python
from auth.oauth import exchange_authorization_code
from auth.token_manager import TokenManager

token_response = exchange_authorization_code("authorization-code-from-procore")
TokenManager().save_oauth_response(token_response)
```

After that, SDK clients call:

```python
from auth.token_manager import get_access_token

access_token = get_access_token()
```

Expired access tokens refresh automatically when a refresh token is available.

## CLI Examples

```bash
.venv/bin/python app.py companies
.venv/bin/python app.py projects
.venv/bin/python app.py rfis --project 352338
.venv/bin/python app.py rfi --project 352338 --id 102784
.venv/bin/python app.py submittals --project 352338
.venv/bin/python app.py submittal --project 352338 --id 309641
.venv/bin/python app.py download-rfi --project 352338 --id 102784
.venv/bin/python app.py download-submittal --project 352338 --id 309641
```

The CLI prints nicely formatted JSON. Typed SDK models are serialized with
`model_dump(mode="json")`.

## SDK Examples

```python
from services import (
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

All typed models can be serialized back to JSON:

```python
json_payload = rfi.model_dump(mode="json")
json_string = rfi.model_dump_json()
```

## Downloading Attachments

RFI attachments are read from:

```text
questions[].attachments[].url
```

Submittal attachments are read from:

```text
attachments[].url
```

Download from services:

```python
rfi_files = download_rfi_attachments(project_id=352338, rfi_id=102784)
submittal_files = download_submittal_attachments(
    project_id=352338,
    submittal_id=309641,
)
```

The shared file service supports safe filenames, streaming writes, retries,
progress logging, batch downloads, and skip-existing behavior by default.

```python
from services.files import FileDownloadService

files = FileDownloadService().download_attachments(
    attachments,
    "downloads/custom",
    fallback_prefix="attachment",
    overwrite=False,
)
```

## Pagination

Collection service methods use `ProcoreClient.get_all()`, which follows Procore
pagination headers automatically. Business logic should call the service method
or `get_all()` and should not manually request page 2.

## Logging

The SDK writes structured logs to:

```text
logs/sdk.log
logs/errors.log
```

API request logs include method, endpoint, response status, elapsed time, and
retry count. Exception logs include stack traces, exception type, request URL,
HTTP status, and response body when available.

The logger redacts sensitive keys such as authorization headers, access tokens,
refresh tokens, and client secrets.

## Architecture

- `auth/`: OAuth exchange, token persistence, token refresh
- `core/`: configuration, endpoint paths, HTTP client, logging, exceptions
- `models/`: Pydantic response models
- `services/`: company, project, RFI, submittal, and file services
- `parser/`: email parsing utilities for future automation
- `tests/`: mocked unit tests with no live Procore dependency

## Verified Endpoint Assumptions

- `GET /rest/v1.0/companies`
- `GET /rest/v1.0/companies/{company_id}/projects`
- `GET /rest/v1.1/projects/{project_id}/rfis`
- `GET /rest/v1.1/projects/{project_id}/rfis/{rfi_id}`
- `GET /rest/v1.1/projects/{project_id}/submittals`
- `GET /rest/v1.1/projects/{project_id}/submittals/{submittal_id}`

## Troubleshooting

`ConfigurationError`
: Check that `.env` exists and all required keys are present.

`AuthenticationError`
: Complete the first OAuth code exchange and confirm `auth/token_store.json`
contains a refresh token.

`AuthorizationError`
: Confirm the Procore user has access to the target company/project/resource.

`ResourceNotFoundError`
: Confirm project, RFI, or submittal IDs are correct for the configured company.

Attachment files are not downloading
: Check `logs/errors.log` for HTTP status and response body details. Existing
files are skipped unless `overwrite=True`.

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

