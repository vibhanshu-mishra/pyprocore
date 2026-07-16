"""Safe structure for a scheduled Data Connection App export (no live calls)."""

from __future__ import annotations


def scheduled_export_plan() -> dict[str, object]:
    """Describe an enterprise export job without credentials or network access."""
    return {
        "auth_mode": "client_credentials",
        "required_environment": [
            "PROCORE_CLIENT_ID",
            "PROCORE_CLIENT_SECRET",
            "PROCORE_LOGIN_URL",
            "PROCORE_API_BASE",
            "PROCORE_COMPANY_ID",
        ],
        "operations": [
            "validate config",
            "request/reuse token",
            "export",
            "encrypt/store",
            "audit",
        ],
        "notes": "Use a secret manager, least-privilege service-account permissions, and matching environment URLs.",
    }


if __name__ == "__main__":
    print(scheduled_export_plan())
