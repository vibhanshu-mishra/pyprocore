"""Phase 9C token-store backend and credential rotation tests."""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
import time
import unittest
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from pyprocore import __version__
from pyprocore.app import (
    AuthRotationChecklistResult,
    TokenStoreClearResult,
    build_auth_rotation_checklist,
    build_parser,
    clear_token_store_cli,
    format_auth_rotation_checklist,
    format_token_store_diagnostic,
    main,
    run_command,
    token_store_sample_paths,
)
from pyprocore.auth.permissions import (
    build_credential_rotation_checklist,
    explain_credential_rotation,
    explain_sandbox_production_separation,
    explain_token_clearance,
)
from pyprocore.auth.token_manager import TokenManager
from pyprocore.auth.token_store import (
    FileTokenStoreBackend,
    MemoryTokenStoreBackend,
    StoredToken,
    TokenStore,
    TokenStoreDiagnostic,
    check_token_store_permissions,
    diagnose_token_store,
    explain_token_store_risk,
    inspect_token_store,
    is_path_inside_project,
)
from pyprocore.core.config import AuthMode, ProcoreSettings
from pyprocore.core.exceptions import AuthenticationError, ConfigurationError


class Phase9CTokenStoreTests(unittest.TestCase):
    """Validate Phase 9C local token-store safety behavior."""

    root = Path(__file__).resolve().parents[1]

    def _token(self, *, auth_mode: str = "authorization_code") -> StoredToken:
        """Return a placeholder token for tests."""
        return StoredToken(
            access_token="placeholder-access-token",
            refresh_token=(
                None if auth_mode == "client_credentials" else "placeholder-refresh-token"
            ),
            expires_at=int(time.time()) + 3600,
            auth_mode=auth_mode,
        )

    def test_file_backend_round_trip_and_safe_permissions(self) -> None:
        """File backends should persist tokens and set private permissions where possible."""
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "token_store.json"
            backend = FileTokenStoreBackend(path)
            store = TokenStore(backend=backend)
            store.save(self._token())

            loaded = store.load()
            self.assertIsNotNone(loaded)
            assert loaded is not None
            self.assertEqual(loaded.access_token.get_secret_value(), "placeholder-access-token")
            self.assertTrue(store.exists())
            self.assertIn("file token store", store.describe_backend())
            mode = path.stat().st_mode & 0o777
            self.assertFalse(mode & 0o077)

    def test_memory_backend_is_process_local(self) -> None:
        """Memory backends should never write token files."""
        backend = MemoryTokenStoreBackend()
        store = TokenStore(backend=backend)
        self.assertFalse(store.exists())
        store.save(self._token(auth_mode="client_credentials"))
        diagnostic = store.diagnostics()
        self.assertTrue(store.exists())
        self.assertEqual(diagnostic.backend_type, "memory")
        self.assertEqual(diagnostic.auth_mode, "client_credentials")
        self.assertIn("tests/examples", " ".join(diagnostic.warnings))
        store.clear()
        self.assertIsNone(store.load())

    def test_missing_malformed_empty_and_legacy_token_store_diagnostics(self) -> None:
        """Diagnostics should safely report common token-store states."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            missing = inspect_token_store(root / "missing.json")
            self.assertEqual(missing.token_status, "Missing")
            self.assertFalse(missing.exists)

            malformed_path = root / "malformed.json"
            malformed_path.write_text("{bad-json", encoding="utf-8")
            malformed = inspect_token_store(malformed_path)
            self.assertEqual(malformed.token_status, "Malformed")
            self.assertTrue(malformed.errors)

            empty_path = root / "empty.json"
            empty_path.write_text("{}", encoding="utf-8")
            empty = inspect_token_store(empty_path)
            self.assertEqual(empty.token_status, "Empty")

            legacy_path = root / "legacy.json"
            legacy_path.write_text(
                json.dumps(
                    {
                        "access_token": "placeholder-access-token",
                        "refresh_token": "placeholder-refresh-token",
                        "expires_at": int(time.time()) + 3600,
                    }
                ),
                encoding="utf-8",
            )
            legacy = diagnose_token_store(legacy_path)
            self.assertEqual(legacy.auth_mode, "authorization_code")
            self.assertTrue(any("auth_mode metadata" in warning for warning in legacy.warnings))
            formatted = format_token_store_diagnostic(legacy)
            self.assertNotIn("placeholder-access-token", formatted)
            self.assertNotIn("placeholder-refresh-token", formatted)

            list_path = root / "list.json"
            list_path.write_text("[]", encoding="utf-8")
            list_diagnostic = inspect_token_store(list_path)
            self.assertEqual(list_diagnostic.token_status, "Malformed")
            self.assertIn("must be an object", " ".join(list_diagnostic.errors))

            invalid_path = root / "invalid.json"
            invalid_path.write_text(
                json.dumps({"access_token": "placeholder-access-token"}),
                encoding="utf-8",
            )
            invalid = inspect_token_store(invalid_path)
            self.assertEqual(invalid.token_status, "Invalid")
            self.assertIn("invalid token metadata", " ".join(invalid.errors))

    def test_risky_path_and_permission_warnings_are_safe(self) -> None:
        """Risk helpers should warn without exposing token contents."""
        repo_token = self.root / "pyprocore/auth/token_store.json"
        self.assertTrue(is_path_inside_project(repo_token, self.root))
        self.assertTrue(explain_token_store_risk(repo_token))
        self.assertTrue(explain_token_store_risk(self.root / ".env"))

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "broad.json"
            path.write_text("{}", encoding="utf-8")
            try:
                path.chmod(0o644)
            except OSError:
                self.skipTest("Platform does not support chmod for this test.")
            warnings = check_token_store_permissions(path)
            self.assertTrue(any("permissions" in warning for warning in warnings))
            self.assertEqual(check_token_store_permissions(path.parent), [])
            self.assertFalse(is_path_inside_project(Path("/tmp/pyprocore-token.json"), None))

    def test_file_backend_clear_refuses_directories(self) -> None:
        """Clear should remove files only, never directories."""
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            store = TokenStore(path)
            with self.assertRaises(AuthenticationError):
                store.clear()
            self.assertTrue(path.exists())

    def test_cli_token_store_commands_are_safe(self) -> None:
        """CLI token-store commands should not print token values."""
        parser = build_parser()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "token.json"
            TokenStore(path).save(self._token())

            status_args = parser.parse_args(["token-store", "status", "--path", str(path)])
            status = run_command(status_args)
            self.assertTrue(status.contains_token)
            formatted = format_token_store_diagnostic(status)
            self.assertIn("Access token: Present", formatted)
            self.assertNotIn("placeholder-access-token", formatted)

            inspect_args = parser.parse_args(
                ["token-store", "inspect", "--path", str(path), "--json"]
            )
            self.assertTrue(run_command(inspect_args).contains_token)

            clear_args = parser.parse_args(["token-store", "clear", "--path", str(path), "--yes"])
            clear_result = run_command(clear_args)
            self.assertTrue(clear_result.cleared)
            self.assertFalse(path.exists())

            missing_args = parser.parse_args(["token-store", "status", "--path", str(path)])
            missing = run_command(missing_args)
            self.assertEqual(missing.token_status, "Missing")
            missing_output = format_token_store_diagnostic(missing)
            self.assertIn("Access token: Missing", missing_output)

    def test_main_token_store_json_and_clear_outputs_are_safe(self) -> None:
        """Main should format token-store JSON and clear outputs without secrets."""
        parser = build_parser()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "token.json"
            TokenStore(path).save(self._token())

            with (
                patch(
                    "pyprocore.app.build_parser",
                    return_value=parser,
                ),
                patch(
                    "sys.argv",
                    ["procore-sdk", "token-store", "inspect", "--path", str(path), "--json"],
                ),
                patch("sys.stdout", new_callable=StringIO) as stdout,
            ):
                with self.assertRaises(SystemExit) as raised:
                    main()
            self.assertEqual(raised.exception.code, 0)
            self.assertIn('"contains_token": true', stdout.getvalue())
            self.assertNotIn("placeholder-access-token", stdout.getvalue())

            TokenStore(path).save(self._token())
            with (
                patch("pyprocore.app.build_parser", return_value=parser),
                patch(
                    "sys.argv",
                    [
                        "procore-sdk",
                        "token-store",
                        "clear",
                        "--path",
                        str(path),
                        "--yes",
                        "--json",
                    ],
                ),
                patch("sys.stdout", new_callable=StringIO) as stdout,
            ):
                main()
            self.assertIn('"cleared": true', stdout.getvalue())
            self.assertFalse(path.exists())

    def test_main_rotation_and_sample_outputs_are_safe(self) -> None:
        """Main should print Phase 9C text commands safely."""
        parser = build_parser()
        with (
            patch("pyprocore.app.build_parser", return_value=parser),
            patch(
                "sys.argv",
                ["procore-sdk", "auth", "rotation-checklist", "--auth-mode", "authorization_code"],
            ),
            patch("sys.stdout", new_callable=StringIO) as stdout,
        ):
            main()
        self.assertIn("Credential Rotation Checklist", stdout.getvalue())

        with (
            patch("pyprocore.app.build_parser", return_value=parser),
            patch(
                "sys.argv",
                ["procore-sdk", "token-store", "sample-paths"],
            ),
            patch("sys.stdout", new_callable=StringIO) as stdout,
        ):
            main()
        self.assertIn("Safe token-store path examples", stdout.getvalue())

    def test_cli_token_store_clear_requires_confirmation(self) -> None:
        """Token-store clear should not delete without confirmation."""
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "token.json"
            TokenStore(path).save(self._token())
            with patch("builtins.input", return_value="no"):
                result = clear_token_store_cli(path, confirmed=False)
            self.assertFalse(result.cleared)
            self.assertTrue(path.exists())

            with patch("builtins.input", return_value="CLEAR"):
                result = clear_token_store_cli(path, confirmed=False)
            self.assertTrue(result.cleared)
            self.assertFalse(path.exists())

    def test_rotation_guidance_for_both_auth_modes(self) -> None:
        """Rotation guidance should be mode-aware and local-only."""
        auth_code = build_auth_rotation_checklist("authorization_code")
        client_credentials = build_auth_rotation_checklist("client_credentials")

        self.assertIn("authorization code", auth_code.summary.casefold())
        self.assertIn("Data Connection App", client_credentials.summary)
        self.assertIn("reauthorize", explain_token_clearance("authorization_code").casefold())
        self.assertIn("fresh token", explain_token_clearance("client_credentials"))
        self.assertIn(
            "sandbox and production",
            explain_sandbox_production_separation().casefold(),
        )
        self.assertTrue(build_credential_rotation_checklist("authorization_code"))
        self.assertTrue(build_credential_rotation_checklist("client_credentials"))
        self.assertIn(
            "No Procore API calls",
            format_auth_rotation_checklist(client_credentials),
        )
        self.assertNotIn("client_secret", explain_credential_rotation("client_credentials"))

        with patch("pyprocore.app.get_settings", side_effect=ConfigurationError("boom")):
            fallback = build_auth_rotation_checklist(None)
        self.assertEqual(fallback.auth_mode, "authorization_code")

        empty = AuthRotationChecklistResult(
            auth_mode="authorization_code",
            summary="summary",
            checklist=[],
            token_clearance="clearance",
            environment_separation="separate",
        )
        self.assertIn("Checklist:", format_auth_rotation_checklist(empty))

    def test_cli_rotation_and_sample_paths(self) -> None:
        """CLI rotation and sample-path commands should be local text."""
        parser = build_parser()
        rotation_args = parser.parse_args(
            ["auth", "rotation-checklist", "--auth-mode", "client_credentials"]
        )
        rotation = run_command(rotation_args)
        self.assertEqual(rotation.auth_mode, "client_credentials")

        sample_args = parser.parse_args(["token-store", "sample-paths"])
        sample = run_command(sample_args)
        self.assertIn("PROCORE_TOKEN_STORE_PATH", sample)
        self.assertNotIn("access_token", sample)
        self.assertIn("Windows", token_store_sample_paths())

    def test_token_store_result_models_and_diagnostics_helpers(self) -> None:
        """Result models and diagnostics helpers should stay serializable."""
        clear_result = TokenStoreClearResult(cleared=False, path="x", message="not cleared")
        self.assertFalse(clear_result.cleared)
        diagnostic = TokenStoreDiagnostic(
            backend_type="file",
            description="desc",
            readable=True,
            contains_token=True,
        )
        self.assertTrue(diagnostic.is_usable)
        errored = TokenStoreDiagnostic(
            backend_type="file",
            description="desc",
            readable=True,
            contains_token=True,
            errors=["bad"],
        )
        self.assertFalse(errored.is_usable)

    def test_token_manager_builds_configured_backends(self) -> None:
        """TokenManager should honor Phase 9C token-store settings."""
        settings = ProcoreSettings(
            client_id="client-id",
            client_secret="client-secret",
            redirect_uri="http://localhost",
            login_url="https://login.example.com",
            api_base="https://api.example.com",
            company_id=123,
            token_store_backend="memory",
        )
        manager = TokenManager(
            oauth_client=object(),  # type: ignore[arg-type]
            settings=settings,
        )
        self.assertIn("memory token store", manager._token_store.describe_backend())

        with tempfile.TemporaryDirectory() as directory:
            token_path = Path(directory) / "configured-token.json"
            file_settings = settings.model_copy(
                update={
                    "token_store_backend": "file",
                    "token_store_path": str(token_path),
                    "auth_mode": AuthMode.AUTHORIZATION_CODE,
                }
            )
            file_manager = TokenManager(
                oauth_client=object(),  # type: ignore[arg-type]
                settings=file_settings,
            )
            self.assertEqual(file_manager._token_store.path, token_path)

    def test_token_store_env_path_and_config_placeholders(self) -> None:
        """Environment overrides and .env.example should remain safe."""
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "env-token.json"
            with patch.dict(os.environ, {"PROCORE_TOKEN_STORE_PATH": str(path)}):
                self.assertEqual(TokenStore().path, path)

        example = (self.root / ".env.example").read_text(encoding="utf-8")
        self.assertIn("PROCORE_TOKEN_STORE_BACKEND=file", example)
        self.assertIn("PROCORE_TOKEN_STORE_PATH=", example)
        self.assertNotIn("placeholder-access-token", example)

    def test_no_phase9c_safety_boundary_regressions(self) -> None:
        """Phase 9C should not alter release or execution boundaries."""
        self.assertEqual(__version__, "2.3.0")
        tracked = subprocess.run(
            ["git", "ls-files", "token_store.json", "pyprocore/auth/token_store.json"],
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertEqual(tracked.stdout.strip(), "")

        workflows = list((self.root / ".github/workflows").glob("*"))
        for path in workflows:
            if path.is_file():
                content = path.read_text(encoding="utf-8")
                self.assertNotIn("token-store clear", content)

        combined_sources = "\n".join(
            path.read_text(encoding="utf-8")
            for path in [
                self.root / "pyprocore/auth/token_store.py",
                self.root / "scripts/check_token_store_safety.py",
            ]
        )
        forbidden = ("boto3", "azure.keyvault", "google.cloud.secretmanager")
        for marker in forbidden:
            self.assertNotIn(marker, combined_sources)

        docs = (self.root / "docs/token-store-and-rotation.md").read_text(encoding="utf-8")
        self.assertIn("Tool execution remains disabled", docs)
        self.assertIn("MCP remains discovery-only", docs)
        self.assertNotIn("Phase 9C is published", docs)


if __name__ == "__main__":
    unittest.main()
