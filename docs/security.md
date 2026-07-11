# Security

PyProcore is designed for local, read-oriented Procore automation. Security still
depends on how carefully credentials, token stores, logs, downloads, and workflow
outputs are handled.

PyProcore is independent open-source software and is not official Procore
support. For Procore account, subscription, permission, or incident questions,
use Procore's official support channels.

## OAuth Credential Safety

Keep these values private:

- `PROCORE_CLIENT_SECRET`
- access tokens
- refresh tokens
- Authorization headers
- OAuth token store files
- screenshots or logs that include credentials

If a client secret, access token, or refresh token is exposed, rotate or revoke
it in Procore before sharing public details.

## `.env` Safety

PyProcore loads `.env` automatically from the current working directory. Do not
commit `.env`, `.env.*`, shell history containing secrets, or CI logs that print
environment values.

Use GitHub Actions secrets or your CI provider's secret store for automation.

## Token Store Safety

PyProcore stores OAuth tokens locally so the SDK can refresh expired access
tokens. The default token store path is:

```text
pyprocore/auth/token_store.json
```

Treat this file like a password file. It is ignored by Git and Docker build
contexts, and CLI diagnostics report only whether tokens are present or missing.
They do not print token values.

## Logs And Download URLs

Structured logs redact sensitive keys such as authorization headers,
`access_token`, `refresh_token`, and `client_secret`. Signed download URLs can
contain query-string credentials, so avoid sharing logs publicly unless you have
reviewed them first.

## Secret Checks

Run the local secret scanner before opening a pull request:

```bash
make secret-check
```

For the broader local quality gate:

```bash
make quality-check
```

The scanner flags likely committed credentials without printing full values. It
ignores documented placeholders such as `your_client_secret`, `example_token`,
and `changeme`.

## Pre-Commit

Optional pre-commit hooks can catch common issues before a commit:

```bash
python3 -m pip install pre-commit
pre-commit install
pre-commit run --all-files
```

Configured hooks include whitespace cleanup, JSON/YAML/TOML checks, large-file
checks, private-key detection, Black, and isort.

## CI Recommendations

CI should run tests, coverage, linting, type checks, formatting checks, release
readiness checks, documentation checks, and secret checks. CI must not require
live Procore credentials for normal pull requests.

## Reporting Security Issues

Do not open public issues for vulnerabilities, leaked credentials, token-store
exposure, or private project data. Use GitHub private vulnerability reporting if
enabled, or contact the maintainer through GitHub without posting exploit or
secret details publicly.
