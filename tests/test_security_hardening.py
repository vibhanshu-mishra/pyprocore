"""Security and quality hardening tests."""

from __future__ import annotations

import json
import subprocess
import sys
import time
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from pyprocore.auth.diagnostics import format_auth_status, get_auth_status
from pyprocore.auth.token_store import TokenStore
from pyprocore.core.doctor import format_doctor_report, run_doctor
from pyprocore.core.logger import sanitize_log_value, structured_message

PROJECT_ROOT = Path(__file__).resolve().parents[1]


class SecurityHardeningTestCase(unittest.TestCase):
    """Validate secret scanning, redaction, and contributor quality hooks."""

    def read_text(self, relative_path: str) -> str:
        """Read a repository file."""
        return (PROJECT_ROOT / relative_path).read_text(encoding="utf-8")

    def test_check_secrets_script_exists(self) -> None:
        """The local secret scanner should be present."""
        self.assertTrue((PROJECT_ROOT / "scripts/check_secrets.py").exists())

    def test_check_secrets_flags_real_looking_secret_without_printing_value(self) -> None:
        """Scanner should fail on likely secrets while hiding the value."""
        with TemporaryDirectory() as temporary_directory:
            secret_file = Path(temporary_directory) / "unsafe.env"
            secret_value = "pc_client_secret_1234567890abcdef"
            secret_file.write_text(
                f"PROCORE_CLIENT_SECRET={secret_value}\n",
                encoding="utf-8",
            )

            result = subprocess.run(
                [sys.executable, "scripts/check_secrets.py", str(secret_file)],
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
                check=False,
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("FAIL", result.stdout)
        self.assertIn("PROCORE_CLIENT_SECRET", result.stdout)
        self.assertNotIn(secret_value, result.stdout)
        self.assertNotIn(secret_value, result.stderr)

    def test_check_secrets_ignores_documented_placeholders(self) -> None:
        """Scanner should allow beginner-friendly placeholder values."""
        with TemporaryDirectory() as temporary_directory:
            placeholder_file = Path(temporary_directory) / "safe.env"
            placeholder_file.write_text(
                "\n".join(
                    [
                        "PROCORE_CLIENT_SECRET=your_client_secret",
                        "access_token=example_token",
                        "refresh_token=changeme",
                        "client_secret=YOUR_CODE_HERE",
                    ]
                ),
                encoding="utf-8",
            )

            result = subprocess.run(
                [sys.executable, "scripts/check_secrets.py", str(placeholder_file)],
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
                check=False,
            )

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("PASS", result.stdout)

    def test_git_and_docker_ignore_secret_paths(self) -> None:
        """Git and Docker ignore rules should cover secrets and token stores."""
        gitignore = self.read_text(".gitignore")
        dockerignore = self.read_text(".dockerignore")

        for ignored in (".env", "token_store.json", "pyprocore/auth/token_store.json"):
            self.assertIn(ignored, gitignore)
            self.assertIn(ignored, dockerignore)

    def test_logging_redacts_sensitive_values(self) -> None:
        """Structured logging should redact tokens, secrets, and signed URL queries."""
        access_token = "example-access-token-1234567890abcdef"
        refresh_token = "example-refresh-token-1234567890abcdef"
        client_secret = "client-secret-1234567890abcdef"
        signed_url = "https://files.example.com/file.pdf?X-Amz-Signature=abc123def456&safe=value"

        message = structured_message(
            "security_test",
            access_token=access_token,
            refresh_token=refresh_token,
            client_secret=client_secret,
            authorization=f"Authorization: Bearer {access_token}",
            request_url=signed_url,
        )

        self.assertNotIn(access_token, message)
        self.assertNotIn(refresh_token, message)
        self.assertNotIn(client_secret, message)
        self.assertNotIn("abc123def456", message)
        self.assertIn("[REDACTED]", message)
        self.assertIn("safe=value", message)

    def test_sanitize_log_value_redacts_nested_token_store_like_payload(self) -> None:
        """Nested token payloads should be safe before logging."""
        payload = {
            "token_store": {
                "access_token": "example-access-token-1234567890abcdef",
                "refresh_token": "example-refresh-token-1234567890abcdef",
            }
        }

        sanitized = sanitize_log_value(payload)

        self.assertEqual(sanitized["token_store"]["access_token"], "[REDACTED]")
        self.assertEqual(sanitized["token_store"]["refresh_token"], "[REDACTED]")

    def test_auth_status_and_doctor_do_not_print_token_values(self) -> None:
        """Diagnostics should report token presence without exposing token values."""
        access_token = "access-token-1234567890abcdef"
        refresh_token = "refresh-token-1234567890abcdef"

        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            env = _required_environment()
            token_path = root / "token_store.json"
            token_path.write_text(
                json.dumps(
                    {
                        "access_token": access_token,
                        "refresh_token": refresh_token,
                        "expires_at": int(time.time()) + 3600,
                    }
                ),
                encoding="utf-8",
            )

            auth_report = get_auth_status(
                token_store=TokenStore(token_path),
                env_path=root / ".env",
                environ=env,
            )
            doctor_report = run_doctor(
                env_path=root / ".env",
                token_store_path=token_path,
                logs_dir=root / "logs",
                downloads_dir=root / "downloads",
                environ=env,
            )

        auth_output = format_auth_status(auth_report)
        doctor_output = format_doctor_report(doctor_report)

        self.assertIn("Access token: Present", auth_output)
        self.assertIn("Refresh token: Present", auth_output)
        self.assertIn("Access token is present.", doctor_output)
        self.assertIn("Refresh token is present.", doctor_output)
        self.assertNotIn(access_token, auth_output)
        self.assertNotIn(refresh_token, auth_output)
        self.assertNotIn(access_token, doctor_output)
        self.assertNotIn(refresh_token, doctor_output)

    def test_pre_commit_config_contains_expected_hooks(self) -> None:
        """Pre-commit config should contain lightweight safety hooks."""
        config = self.read_text(".pre-commit-config.yaml")

        for hook in (
            "trailing-whitespace",
            "end-of-file-fixer",
            "check-yaml",
            "check-json",
            "check-toml",
            "check-added-large-files",
            "detect-private-key",
            "black",
            "isort",
        ):
            self.assertIn(hook, config)

    def test_ci_workflow_is_non_live_and_uses_project_tests(self) -> None:
        """CI should run non-live project checks without Procore secrets."""
        workflow = self.read_text(".github/workflows/tests.yml")

        for command in ("make test", "make coverage"):
            self.assertIn(command, workflow)
        self.assertNotIn("smoke-", workflow)
        self.assertNotIn("PROCORE_CLIENT_SECRET", workflow)

    def test_makefile_has_security_quality_targets(self) -> None:
        """Makefile should expose secret and quality checks."""
        makefile = self.read_text("Makefile")

        self.assertIn("secret-check:", makefile)
        self.assertIn("scripts/check_secrets.py", makefile)
        self.assertIn("quality-check:", makefile)
        self.assertIn("release-check", makefile)

    def test_security_docs_and_readme_cover_secret_safety(self) -> None:
        """Docs should explain token, credential, and scanner safety."""
        docs = self.read_text("docs/security.md")
        readme = self.read_text("README.md")
        security = self.read_text("SECURITY.md")

        for text in (docs, readme, security):
            self.assertIn("token", text.lower())
            self.assertIn("secret", text.lower())
        self.assertIn("make secret-check", docs)
        self.assertIn("make quality-check", readme)
        self.assertIn("token_store.json", security)


def _required_environment() -> dict[str, str]:
    """Return complete test auth configuration."""
    return {
        "PROCORE_CLIENT_ID": "client-id",
        "PROCORE_CLIENT_SECRET": "client-secret",
        "PROCORE_REDIRECT_URI": "http://localhost/callback",
        "PROCORE_LOGIN_URL": "https://login.procore.com",
        "PROCORE_API_BASE": "https://api.procore.com",
        "PROCORE_COMPANY_ID": "123",
    }


if __name__ == "__main__":
    unittest.main()
