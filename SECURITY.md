# Security Policy

## Supported Versions

Security fixes are considered for the latest released version of PyProcore.
Older releases are best effort.

| Version | Supported |
| ------- | --------- |
| Latest release | Yes |
| Older releases | Best effort |

## Reporting a Vulnerability

Please do not open public GitHub issues for security vulnerabilities, leaked
secrets, OAuth problems, token-store exposure, or private project data.

Use GitHub private vulnerability reporting if it is enabled for the repository.
If that is not available, contact the maintainer through GitHub and avoid
posting exploit details publicly.

## Secret Handling

Never share or commit:

- Procore client IDs when paired with other credentials
- Procore client secrets
- access tokens
- refresh tokens
- Authorization headers
- `.env` files
- token store files such as `token_store.json`
- logs or screenshots containing credentials
- private project, company, document, drawing, RFI, or submittal data

## Token Store Warning

PyProcore stores OAuth tokens locally for development workflows. Treat token
store files as secrets. Do not commit them, attach them to issues, or upload them
to CI artifacts.

## Procore OAuth Credential Warning

If a Procore OAuth client secret, refresh token, or access token is exposed,
rotate or revoke it immediately in Procore before sharing any public details.
