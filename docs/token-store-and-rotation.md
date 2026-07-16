# Token Store and Credential Rotation

PyProcore `v2.2.0` remains the current published stable release. Phase 8A
through 8G and Phase 9A through 9C are unreleased branch work unless they are
published in a later release.

Phase 9C adds local token-store safety helpers, backend architecture, and
credential rotation guidance. It does not call Procore, does not call external
AI or model APIs, does not add cloud secret-manager integrations, and does not
enable agent tool execution. MCP remains discovery-only.

## Token Store Basics

The default token store backend is file-based. Existing token-store JSON files
continue to work.

Recommended practice:

- Keep token stores outside the repository.
- Never commit `.env`, token stores, logs, downloads, generated exports, or
  private project data.
- Use `PROCORE_TOKEN_STORE_PATH` to point to a private runtime path.
- Use `PROCORE_TOKEN_STORE_BACKEND=file` for persistent local storage.
- Use `PROCORE_TOKEN_STORE_BACKEND=memory` only for tests and examples.
- Keep sandbox and production token stores separate.

Cloud secret-manager backends are future work unless explicitly implemented in a
later release.

## CLI Checks

Inspect the token store safely:

```bash
procore-sdk token-store status
procore-sdk token-store inspect --json
```

Show suggested private paths:

```bash
procore-sdk token-store sample-paths
```

Clear only the configured token-store file:

```bash
procore-sdk token-store clear --yes
```

Without `--yes`, the command asks for an explicit `CLEAR` confirmation.

## Credential Rotation

Print local-only guidance:

```bash
procore-sdk auth rotation-checklist --auth-mode authorization_code
procore-sdk auth rotation-checklist --auth-mode client_credentials
```

Authorization Code rotation usually means:

- Rotate the OAuth app client secret in Procore if required.
- Update private `.env` or deployment secrets.
- Generate a fresh login URL if app settings changed.
- Exchange a new authorization code when reauthorization is needed.
- Clear old token stores safely.
- Verify the authenticated user's permissions.

Client Credentials rotation usually means:

- Rotate the Data Connection App secret in Procore.
- Update the deployment secret store.
- Clear or replace the old token store.
- Request a new client-credentials token through the normal SDK flow.
- Verify DMSA/app permissions.
- Dry-run scheduled exports after rotation.

## Enterprise Deployment Notes

For scheduled exports and Data Connection App deployments:

- Keep token stores and output folders private.
- Keep production and sandbox credentials fully separate.
- Store client secrets in your deployment platform's private secret store.
- Dry-run scheduled exports after every credential rotation.
- Do not rely on the memory token store for real automation.

Token-store safety applies when users deliberately run SDK or CLI workflows.
Tool execution remains disabled, and the agent registry/MCP adapters remain
metadata and discovery surfaces only.
