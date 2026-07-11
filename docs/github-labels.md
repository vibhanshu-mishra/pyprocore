# Suggested GitHub Labels

These labels are a suggested starting point for the PyProcore repository. They
can be created manually in GitHub repository settings.

| Label | Purpose |
| ----- | ------- |
| `bug` | Something is broken or behaving unexpectedly. |
| `enhancement` | New feature or improvement request. |
| `documentation` | README, docs, recipes, examples, or comments. |
| `good first issue` | Small, well-scoped task for new contributors. |
| `help wanted` | Maintainers would welcome community help. |
| `endpoint request` | Request for a new Procore endpoint/resource. |
| `automation` | Workflow plans, scheduled runs, Docker, CI, or webhook helpers. |
| `auth` | OAuth, token refresh, `.env`, or token-store behavior. |
| `workflows` | AI-ready packages, syncs, exports, or local workflow runner. |
| `breaking change` | Changes that may affect public API compatibility. |
| `security` | Security-sensitive work. Do not discuss private vulnerabilities publicly. |
| `needs reproduction` | Maintainers need a minimal reproduction or more detail. |

## Labeling Tips

- Use `security` only for public-safe tracking. Private vulnerabilities should
  follow `SECURITY.md`.
- Use `endpoint request` when the main ask is adding a Procore REST resource.
- Use `good first issue` only when the issue has enough detail for a new
  contributor to start safely.
- Use `needs reproduction` when logs or examples are missing, but remind users
  not to paste secrets, tokens, `.env` values, or private project data.
