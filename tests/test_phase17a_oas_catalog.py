"""Tests for Phase 17A local OAS-backed safe endpoint catalog support."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import pyprocore
from pyprocore.catalog import (
    CatalogEndpointSafety,
    catalog_endpoints_to_json,
    catalog_endpoints_to_markdown,
    catalog_summary_to_json,
    catalog_summary_to_markdown,
    classify_endpoint_safety,
    compare_catalog_to_pyprocore_supported_coverage,
    coverage_report_to_json,
    coverage_report_to_markdown,
    list_endpoints,
    load_oas_catalog,
    summarize_by_method,
    summarize_by_path_area,
)
from pyprocore.core.exceptions import ValidationError

PROJECT_ROOT = Path(__file__).resolve().parents[1]
FAKE_OAS = PROJECT_ROOT / "examples" / "catalog" / "fake_procore_oas.json"


class Phase17AOASCatalogTests(unittest.TestCase):
    """Validate local-only OAS catalog parsing and safety reporting."""

    def run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        """Run the local CLI without requiring credentials."""
        env = {**os.environ, "PYTHONPATH": str(PROJECT_ROOT)}
        return subprocess.run(
            [sys.executable, "-m", "pyprocore.app", *args],
            cwd=PROJECT_ROOT,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_parse_fake_oas_catalog(self) -> None:
        """Local fake OAS fixture should parse into typed endpoint metadata."""
        catalog = load_oas_catalog(FAKE_OAS)

        self.assertEqual(catalog.title, "Fake Procore OAS Catalog")
        self.assertEqual(catalog.version, "0.0.0-example")
        self.assertEqual(len(catalog.endpoints), 7)
        self.assertEqual(len(list_endpoints(catalog, method="GET")), 4)
        self.assertTrue(hasattr(pyprocore, "load_oas_catalog"))
        self.assertFalse(catalog.execution_enabled)
        self.assertFalse(catalog.remote_fetch_enabled)
        projects = [
            endpoint
            for endpoint in catalog.endpoints
            if endpoint.path == "/rest/v1.0/companies/{company_id}/projects"
        ][0]
        self.assertEqual(projects.path_area, "projects")
        self.assertEqual(projects.parameters[0].name, "company_id")

    def test_method_and_path_area_summaries(self) -> None:
        """Catalog summaries should group endpoints by method and area."""
        catalog = load_oas_catalog(FAKE_OAS)

        self.assertEqual(summarize_by_method(catalog), {"GET": 4, "POST": 2, "TRACE": 1})
        area_counts = summarize_by_path_area(catalog)
        self.assertEqual(area_counts["companies"], 1)
        self.assertEqual(area_counts["projects"], 1)
        self.assertEqual(area_counts["rfis"], 2)

    def test_safety_classification_rules(self) -> None:
        """Read-only methods and risky mutation terms should be classified safely."""
        read_only, read_reasons = classify_endpoint_safety("GET", "/rest/v1.0/companies")
        post, post_reasons = classify_endpoint_safety("POST", "/rest/v1.0/projects")
        patch, _ = classify_endpoint_safety("PATCH", "/rest/v1.0/projects/{id}")
        put, _ = classify_endpoint_safety("PUT", "/rest/v1.0/projects/{id}")
        delete, _ = classify_endpoint_safety("DELETE", "/rest/v1.0/projects/{id}")
        risky_get, risky_reasons = classify_endpoint_safety(
            "GET",
            "/rest/v1.0/projects/{project_id}/payment_applications",
        )
        upload_head, _ = classify_endpoint_safety(
            "HEAD",
            "/rest/v1.0/projects/{project_id}/documents/upload",
        )
        unknown, unknown_reasons = classify_endpoint_safety(
            "TRACE",
            "/rest/v1.0/projects/{project_id}/unknown_widgets",
        )

        self.assertEqual(read_only, CatalogEndpointSafety.READ_ONLY)
        self.assertIn("normally read-only", read_reasons[0])
        for classification in (post, patch, put, delete):
            self.assertEqual(classification, CatalogEndpointSafety.WRITE_OR_MUTATION)
        self.assertIn("mutate Procore data", post_reasons[0])
        self.assertEqual(risky_get, CatalogEndpointSafety.WRITE_OR_MUTATION)
        self.assertIn("payment", risky_reasons[0])
        self.assertEqual(upload_head, CatalogEndpointSafety.WRITE_OR_MUTATION)
        self.assertEqual(unknown, CatalogEndpointSafety.UNKNOWN)
        self.assertIn("not classified", unknown_reasons[0])

    def test_coverage_report_contains_supported_and_unsupported_areas(self) -> None:
        """Coverage reports should separate supported, unsupported, and safety buckets."""
        catalog = load_oas_catalog(FAKE_OAS)
        report = compare_catalog_to_pyprocore_supported_coverage(catalog)

        self.assertIn("companies", report.already_supported_areas)
        self.assertIn("projects", report.already_supported_areas)
        self.assertIn("payment_applications", report.unsupported_areas)
        self.assertEqual(len(report.read_only_candidates), 3)
        self.assertEqual(len(report.risky_write_candidates), 3)
        self.assertEqual(len(report.unknown_candidates), 1)
        self.assertFalse(report.execution_enabled)
        self.assertFalse(report.remote_fetch_enabled)

    def test_json_and_markdown_reports_are_serializable(self) -> None:
        """Catalog summaries, endpoints, and coverage reports should render cleanly."""
        catalog = load_oas_catalog(FAKE_OAS)
        report = compare_catalog_to_pyprocore_supported_coverage(catalog)

        summary_payload = json.loads(catalog_summary_to_json(catalog.summary(), pretty=True))
        endpoints_payload = json.loads(catalog_endpoints_to_json(catalog.endpoints, pretty=True))
        report_payload = json.loads(coverage_report_to_json(report, pretty=True))
        summary_markdown = catalog_summary_to_markdown(catalog.summary())
        endpoints_markdown = catalog_endpoints_to_markdown(catalog.endpoints)
        report_markdown = coverage_report_to_markdown(report)

        self.assertEqual(summary_payload["mode"], "local_oas_metadata_only")
        self.assertEqual(len(endpoints_payload), 7)
        self.assertIn("read_only_candidates", report_payload)
        self.assertIn("OAS Catalog Summary", summary_markdown)
        self.assertIn("OAS Catalog Endpoints", endpoints_markdown)
        self.assertIn("does not call Procore", report_markdown)
        self.assertIn("generate executable clients", report_markdown)

    def test_local_path_validation_rejects_remote_or_invalid_inputs(self) -> None:
        """Catalog loading should never fetch remote OAS files or invalid paths."""
        with self.assertRaisesRegex(ValidationError, "not a URL"):
            load_oas_catalog("https://example.invalid/procore-oas.json")
        with self.assertRaisesRegex(ValidationError, ".json"):
            load_oas_catalog(PROJECT_ROOT / "README.md")
        with self.assertRaisesRegex(ValidationError, "does not exist"):
            load_oas_catalog(PROJECT_ROOT / "examples" / "catalog" / "missing.json")

        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            invalid_json = temp / "invalid.json"
            array_json = temp / "array.json"
            no_paths_json = temp / "no_paths.json"
            invalid_json.write_text("{", encoding="utf-8")
            array_json.write_text("[]", encoding="utf-8")
            no_paths_json.write_text("{}", encoding="utf-8")

            with self.assertRaisesRegex(ValidationError, "not valid JSON"):
                load_oas_catalog(invalid_json)
            with self.assertRaisesRegex(ValidationError, "must be an object"):
                load_oas_catalog(array_json)
            with self.assertRaisesRegex(ValidationError, "paths"):
                load_oas_catalog(no_paths_json)

    def test_cli_catalog_commands_work_without_credentials(self) -> None:
        """Catalog CLI commands should run against local files without Procore access."""
        summarize = self.run_cli("catalog", "summarize", str(FAKE_OAS), "--json")
        endpoints = self.run_cli(
            "catalog",
            "endpoints",
            str(FAKE_OAS),
            "--method",
            "GET",
            "--json",
        )
        coverage = self.run_cli(
            "catalog",
            "coverage-report",
            str(FAKE_OAS),
            "--format",
            "json",
        )
        safety = self.run_cli(
            "catalog",
            "safety-report",
            str(FAKE_OAS),
            "--format",
            "markdown",
        )

        self.assertEqual(summarize.returncode, 0, summarize.stderr)
        self.assertEqual(endpoints.returncode, 0, endpoints.stderr)
        self.assertEqual(coverage.returncode, 0, coverage.stderr)
        self.assertEqual(safety.returncode, 0, safety.stderr)
        self.assertEqual(json.loads(summarize.stdout)["endpoint_count"], 7)
        self.assertEqual(len(json.loads(endpoints.stdout)), 4)
        self.assertIn("unsupported_areas", coverage.stdout)
        self.assertIn("OAS Coverage and Safety Report", safety.stdout)

    def test_catalog_source_does_not_enable_execution_or_network_calls(self) -> None:
        """Catalog code should stay metadata-only and avoid network/tool execution."""
        catalog_sources = "\n".join(
            path.read_text(encoding="utf-8")
            for path in sorted((PROJECT_ROOT / "pyprocore" / "catalog").glob("*.py"))
        )

        forbidden_snippets = (
            "import requests",
            "from requests",
            "import httpx",
            "from httpx",
            "import urllib.request",
            "from urllib",
            "import subprocess",
            "from subprocess",
            "import importlib",
            "from importlib",
            "api.procore.com",
            "procore.com/rest",
            "exec(",
            "eval(",
        )
        for snippet in forbidden_snippets:
            self.assertNotIn(snippet, catalog_sources)
