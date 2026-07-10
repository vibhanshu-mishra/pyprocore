"""Unit tests for Procore drawing services and resolvers."""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from pyprocore.core.exceptions import (
    AuthorizationError,
    MultipleResultsError,
    NotFoundError,
    ResourceNotFoundError,
    ValidationError,
)
from pyprocore.models import Drawing
from pyprocore.services.drawings import (
    DrawingsService,
    download_drawing,
    get_drawing,
    get_drawing_area,
    list_drawing_areas,
    list_drawing_disciplines,
    list_drawings,
)
from pyprocore.services.search import find_drawing, find_drawings_contains


class DrawingsServiceTestCase(unittest.TestCase):
    """Validate drawing services without live Procore access."""

    def test_list_drawing_areas_uses_endpoint_params_and_headers(self) -> None:
        """Area listing calls the endpoint and returns typed models."""
        client = Mock()
        client.get_all.return_value = [{"id": 1, "name": "Area A"}]

        result = DrawingsService(client=client).list_drawing_areas(
            10,
            company_id=123,
            params={"per_page": 50},
            sort="name",
        )

        self.assertEqual(result[0].name, "Area A")
        client.get_all.assert_called_once_with(
            "/rest/v1.0/projects/10/drawing_areas",
            params={"per_page": 50, "sort": "name"},
            headers={"Procore-Company-Id": "123"},
        )

    def test_get_drawing_area_returns_model(self) -> None:
        """Area retrieval calls the endpoint and returns a typed model."""
        client = Mock()
        client.get.return_value = {"id": 2, "name": "Level 2"}

        result = DrawingsService(client=client).get_drawing_area(10, 2)

        self.assertEqual(result.id, 2)
        client.get.assert_called_once_with(
            "/rest/v1.0/projects/10/drawing_areas/2",
            headers=None,
        )

    def test_list_drawing_disciplines_returns_models(self) -> None:
        """Discipline listing returns typed models."""
        client = Mock()
        client.get_all.return_value = [{"id": 3, "name": "Structural", "abbreviation": "S"}]

        result = DrawingsService(client=client).list_drawing_disciplines(10)

        self.assertEqual(result[0].abbreviation, "S")
        client.get_all.assert_called_once_with(
            "/rest/v1.0/projects/10/drawing_disciplines",
            params=None,
            headers=None,
        )

    def test_list_drawings_passes_filters_and_returns_models(self) -> None:
        """Drawing listing passes supported filters through."""
        client = Mock()
        client.get_all.return_value = [{"id": 4, "number": "S-101", "title": "Framing Plan"}]

        result = DrawingsService(client=client).list_drawings(
            10,
            company_id=123,
            drawing_area_id=5,
            discipline_id=6,
            current=True,
            params={"per_page": 100},
        )

        self.assertEqual(result[0], Drawing(id=4, number="S-101", title="Framing Plan"))
        client.get_all.assert_called_once_with(
            "/rest/v1.0/drawing_areas/5/drawings",
            params={
                "per_page": 100,
                "discipline_id": 6,
                "current": True,
            },
            headers={"Procore-Company-Id": "123"},
        )

    def test_list_drawings_without_area_lists_across_areas(self) -> None:
        """Project-level drawing listing walks drawing areas internally."""
        client = Mock()
        client.get_all.side_effect = [
            [{"id": 5, "name": "Area A"}, {"id": 6, "name": "Area B"}],
            [{"id": 4, "number": "S-101"}],
            [{"id": 7, "number": "A-101"}],
        ]

        result = DrawingsService(client=client).list_drawings(10, current=True)

        self.assertEqual([drawing.id for drawing in result], [4, 7])
        self.assertEqual(
            client.get_all.call_args_list[0].args[0], "/rest/v1.0/projects/10/drawing_areas"
        )
        self.assertEqual(
            client.get_all.call_args_list[1].args[0], "/rest/v1.0/drawing_areas/5/drawings"
        )
        self.assertEqual(
            client.get_all.call_args_list[2].args[0], "/rest/v1.0/drawing_areas/6/drawings"
        )

    def test_get_drawing_returns_model(self) -> None:
        """Drawing retrieval calls the endpoint and returns a typed model."""
        client = Mock()
        client.get.return_value = {"id": 4, "number": "A-101"}

        result = DrawingsService(client=client).get_drawing(10, 4, drawing_area_id=5)

        self.assertEqual(result.number, "A-101")
        client.get.assert_called_once_with(
            "/rest/v1.0/drawing_areas/5/drawings/4",
            headers=None,
        )

    def test_get_drawing_without_area_finds_area_first(self) -> None:
        """Drawing retrieval can preserve the older project-only call style."""
        client = Mock()
        client.get_all.side_effect = [
            [{"id": 5, "name": "Area A"}],
            [{"id": 4, "number": "A-101"}],
        ]
        client.get.return_value = {"id": 4, "number": "A-101"}

        result = DrawingsService(client=client).get_drawing(10, 4)

        self.assertEqual(result.id, 4)
        client.get.assert_called_once_with(
            "/rest/v1.0/drawing_areas/5/drawings/4",
            headers=None,
        )

    def test_get_drawing_without_area_raises_when_missing(self) -> None:
        """Project-only drawing lookup raises a clear not-found error."""
        client = Mock()
        client.get_all.side_effect = [
            [{"id": 5, "name": "Area A"}],
            [{"id": 9, "number": "A-102"}],
        ]

        with self.assertRaisesRegex(NotFoundError, "Drawing 4 was not found"):
            DrawingsService(client=client).get_drawing(10, 4)

    def test_object_responses_are_required_for_getters(self) -> None:
        """Unexpected single-resource payloads fail clearly."""
        client = Mock()
        client.get.return_value = []

        with self.assertRaisesRegex(ValidationError, "drawing response"):
            DrawingsService(client=client).get_drawing(10, 4, drawing_area_id=5)
        with self.assertRaisesRegex(ValidationError, "drawing area response"):
            DrawingsService(client=client).get_drawing_area(10, 4)

    def test_download_drawing_uses_file_service(self) -> None:
        """Drawing downloads delegate streaming to the shared file service."""
        client = Mock()
        client.get.return_value = {
            "id": 4,
            "number": "S-101",
            "download_url": "https://signed.example/drawing.pdf",
        }
        file_service = Mock()
        file_service.download_url.return_value = Path("drawings/S-101.pdf")

        result = DrawingsService(client=client, file_service=file_service).download_drawing(
            10,
            4,
            output_dir="drawings",
            overwrite=True,
            drawing_area_id=5,
        )

        self.assertEqual(result, Path("drawings/S-101.pdf"))
        file_service.download_url.assert_called_once_with(
            "https://signed.example/drawing.pdf",
            Path("drawings") / "S-101.pdf",
            overwrite=True,
        )

    def test_download_drawing_prefers_explicit_filename(self) -> None:
        """A caller-provided filename overrides drawing metadata."""
        client = Mock()
        client.get.return_value = {"id": 4, "url": "https://signed.example/drawing"}
        file_service = Mock()

        DrawingsService(client=client, file_service=file_service).download_drawing(
            10,
            4,
            output_dir="drawings",
            filename="plan?.pdf",
            drawing_area_id=5,
        )

        file_service.download_url.assert_called_once_with(
            "https://signed.example/drawing",
            Path("drawings") / "plan_.pdf",
            overwrite=False,
        )

    def test_download_drawing_requires_url(self) -> None:
        """Drawings without a URL fail before trying to download."""
        client = Mock()
        client.get.return_value = {"id": 4, "number": "S-101"}
        file_service = Mock()

        with self.assertRaisesRegex(ValidationError, "download URL"):
            DrawingsService(client=client, file_service=file_service).download_drawing(
                10,
                4,
                drawing_area_id=5,
            )

        file_service.download_url.assert_not_called()

    def test_service_functions_delegate_to_service(self) -> None:
        """Module-level helpers preserve the existing service style."""
        with patch("pyprocore.services.drawings.DrawingsService") as service_cls:
            service = service_cls.return_value
            service.list_drawing_areas.return_value = ["area"]
            service.get_drawing_area.return_value = "area"
            service.list_drawing_disciplines.return_value = ["discipline"]
            service.list_drawings.return_value = ["drawing"]
            service.get_drawing.return_value = "drawing"
            service.download_drawing.return_value = Path("drawing.pdf")

            self.assertEqual(list_drawing_areas(10), ["area"])
            self.assertEqual(get_drawing_area(10, 1), "area")
            self.assertEqual(list_drawing_disciplines(10), ["discipline"])
            self.assertEqual(list_drawings(10, drawing_area_id=2), ["drawing"])
            self.assertEqual(get_drawing(10, 3), "drawing")
            self.assertEqual(download_drawing(10, 3), Path("drawing.pdf"))

        service.list_drawing_areas.assert_called_once_with(
            10,
            company_id=None,
            params=None,
        )
        service.get_drawing_area.assert_called_once_with(10, 1, company_id=None)
        service.list_drawing_disciplines.assert_called_once_with(
            10,
            company_id=None,
            params=None,
        )
        service.list_drawings.assert_called_once_with(
            10,
            company_id=None,
            drawing_area_id=2,
            discipline_id=None,
            current=None,
            params=None,
        )
        service.get_drawing.assert_called_once_with(
            10,
            3,
            company_id=None,
            drawing_area_id=None,
        )
        service.download_drawing.assert_called_once()

    def test_positive_ids_are_validated(self) -> None:
        """Drawing services validate IDs before making requests."""
        service = DrawingsService(client=Mock())

        with self.assertRaises(ValidationError):
            service.list_drawings(0)
        with self.assertRaises(ValidationError):
            service.list_drawings(10, drawing_area_id=0)
        with self.assertRaises(ValidationError):
            service.get_drawing(10, 0)


class DrawingResolverTestCase(unittest.TestCase):
    """Validate human-friendly drawing resolvers."""

    @patch("pyprocore.services.search.list_drawings")
    def test_find_drawing_matches_case_insensitive_number(self, drawings: Mock) -> None:
        """Drawing resolver supports exact case-insensitive number matching."""
        drawings.return_value = [Drawing(id=1, number="S-101", title="Framing Plan")]

        result = find_drawing(10, number="s-101", company_id=123)

        self.assertEqual(result.id, 1)
        drawings.assert_called_once_with(10, company_id=123)

    @patch("pyprocore.services.search.list_drawings")
    def test_find_drawing_matches_partial_title(self, drawings: Mock) -> None:
        """Drawing resolver supports partial title matching."""
        drawings.return_value = [Drawing(id=1, number="S-101", title="Framing Plan")]

        result = find_drawing(10, title="framing")

        self.assertEqual(result.id, 1)

    @patch("pyprocore.services.search.list_drawings")
    def test_find_drawing_raises_for_multiple_partial_matches(self, drawings: Mock) -> None:
        """Ambiguous drawing searches raise the shared multiple-results error."""
        drawings.return_value = [
            Drawing(id=1, number="A-101", title="Floor Plan"),
            Drawing(id=2, number="A-102", title="Roof Plan"),
        ]

        with self.assertRaises(MultipleResultsError):
            find_drawing(10, title="plan")

    @patch("pyprocore.services.search.list_drawings")
    def test_find_drawings_contains_returns_multiple_matches(self, drawings: Mock) -> None:
        """Contains search returns all matching drawings."""
        drawings.return_value = [
            Drawing(id=1, number="A-101", title="Floor Plan"),
            Drawing(id=2, number="S-101", title="Framing Plan"),
            Drawing(id=3, number="C-001", title="Civil Notes"),
        ]

        result = find_drawings_contains(10, "plan", company_id=123)

        self.assertEqual([drawing.id for drawing in result], [1, 2])
        drawings.assert_called_once_with(10, company_id=123)

    @patch("pyprocore.services.search.list_drawings")
    def test_find_drawings_contains_raises_for_no_match(self, drawings: Mock) -> None:
        """Contains search raises not-found when nothing matches."""
        drawings.return_value = [Drawing(id=1, number="A-101", title="Floor Plan")]

        with self.assertRaises(NotFoundError):
            find_drawings_contains(10, "missing")

    def test_find_drawing_requires_one_query_field(self) -> None:
        """Drawing resolver validates query choices."""
        with self.assertRaises(ValueError):
            find_drawing(10)
        with self.assertRaises(ValueError):
            find_drawing(10, number="A-101", title="Floor")


class DrawingsSmokeScriptTestCase(unittest.TestCase):
    """Validate the manual Drawings smoke script without live API access."""

    def test_smoke_script_prints_friendly_404_guidance(self) -> None:
        """A Procore 404 includes project, tool, and environment guidance."""
        module = _load_smoke_drawings_module()
        client = Mock()
        client.get_all.side_effect = ResourceNotFoundError(
            "Resource not found",
            status_code=404,
        )

        with (
            patch.object(module, "ProcoreClient", return_value=client),
            patch.object(sys, "argv", ["smoke_drawings.py", "--project", "10"]),
            patch("builtins.print") as mocked_print,
        ):
            exit_code = module.main()

        output = "\n".join(str(call.args[0]) for call in mocked_print.call_args_list if call.args)
        self.assertEqual(exit_code, 1)
        self.assertIn("reached Procore", output)
        self.assertIn("sandbox vs production API base", output)
        self.assertIn("Drawings tool", output)

    def test_smoke_script_prints_friendly_403_context_guidance(self) -> None:
        """A Procore 403 explains project/company context instead of OAuth failure."""
        module = _load_smoke_drawings_module()
        client = Mock()
        client.get_all.side_effect = AuthorizationError(
            "Procore API request failed with status 403: Invalid Project or Company"
        )

        with (
            patch.object(module, "ProcoreClient", return_value=client),
            patch.object(sys, "argv", ["smoke_drawings.py", "--project", "10"]),
            patch("builtins.print") as mocked_print,
        ):
            exit_code = module.main()

        output = "\n".join(str(call.args[0]) for call in mocked_print.call_args_list if call.args)
        self.assertEqual(exit_code, 1)
        self.assertIn(
            "Authenticated successfully, but Procore rejected the project/company context.",
            output,
        )
        self.assertIn("Confirm project_id belongs to company_id", output)
        self.assertIn("Confirm production vs sandbox environment", output)
        self.assertIn("OAuth user has access to the company/project", output)
        self.assertIn("Drawings tool is enabled", output)
        self.assertIn("permission to view Drawings", output)
        self.assertNotIn("could not authenticate with Procore", output)


def _load_smoke_drawings_module() -> object:
    """Load the manual smoke script as a module for safe unit testing."""
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "smoke_drawings.py"
    spec = importlib.util.spec_from_file_location("smoke_drawings_test_module", script_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load smoke_drawings.py for testing.")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


if __name__ == "__main__":
    unittest.main()
