# Contributing

Thanks for helping improve PyProcore.

PyProcore welcomes practical fixes, documentation improvements, examples, tests,
and carefully scoped endpoint additions. Keep changes additive when possible and
avoid breaking existing public SDK interfaces.

## Local Development

Set up the project from source:

```bash
git clone https://github.com/vibhanshu-mishra/pyprocore.git
cd pyprocore
python3 -m venv .venv
python3 -m pip install --upgrade pip
python3 -m pip install -e ".[dev]"
```

Useful checks:

```bash
make examples-check
make test
make coverage
make lint
make typecheck
python3 -m black --check .
python3 -m isort --check-only .
```

## Pull Requests

Before opening a pull request:

- keep the change focused
- add or update tests
- update docs and examples when behavior changes
- update the changelog when the change is user-visible
- avoid live Procore calls in tests
- never commit secrets or private project data

## Security And Support

Do not paste Procore client secrets, access tokens, refresh tokens, `.env`
values, token stores, Authorization headers, or private project data into public
issues or pull requests.

PyProcore is an independent open-source project and is not official Procore
support. For Procore account, permission, subscription, or production incident
questions, contact Procore through official support channels.

## Community Docs

The full repository-level community docs are available on GitHub:

- [Contributing guide](https://github.com/vibhanshu-mishra/pyprocore/blob/main/CONTRIBUTING.md)
- [Code of Conduct](https://github.com/vibhanshu-mishra/pyprocore/blob/main/CODE_OF_CONDUCT.md)
- [Security policy](https://github.com/vibhanshu-mishra/pyprocore/blob/main/SECURITY.md)
- [Support guide](https://github.com/vibhanshu-mishra/pyprocore/blob/main/SUPPORT.md)
- [Suggested GitHub labels](github-labels.md)
