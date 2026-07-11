"""Unit tests for Procore Daily Logs services."""

from __future__ import annotations

import unittest
from unittest.mock import Mock, patch

from pyprocore.core.exceptions import NotFoundError, ValidationError
from pyprocore.services.daily_logs import (
    DAILY_LOG_PATHS,
    DAILY_LOG_TYPES,
    DailyLogsService,
    get_daily_log,
    get_daily_log_counts,
    get_daily_log_header,
    list_daily_log_headers,
    list_daily_logs,
    list_daily_logs_for_date,
    list_delay_log_types,
    list_manpower_logs,
    list_notes_logs,
)


class DailyLogsServiceTestCase(unittest.TestCase):
    """Validate Daily Logs services without live Procore access."""

    def test_log_type_constants_include_known_paths(self) -> None:
        """Known Daily Log types are exported for callers."""
        self.assertIn("manpower", DAILY_LOG_TYPES)
        self.assertEqual(DAILY_LOG_PATHS["notes"], "notes_logs")

    def test_counts_uses_v11_path_and_company_header(self) -> None:
        """Counts endpoint uses v1.1 path and shared filters."""
        client = Mock()
        client.get.return_value = {"manpower": 2, "notes": 1}

        result = DailyLogsService(client=client).get_daily_log_counts(
            456,
            company_id=123,
            log_date="2026-07-10",
            params={"ignored": None},
            custom="yes",
        )

        self.assertEqual(result[0].log_type, "manpower")
        client.get.assert_called_once_with(
            "/rest/v1.1/projects/456/daily_logs/counts",
            params={"custom": "yes", "log_date": "2026-07-10"},
            headers={"Procore-Company-Id": "123"},
        )

    @patch("pyprocore.services.daily_logs.get_settings")
    def test_company_id_defaults_to_settings(self, get_settings: Mock) -> None:
        """Daily Logs services default to PROCORE_COMPANY_ID."""
        get_settings.return_value.company_id = 321
        client = Mock()
        client.get_all.return_value = []

        DailyLogsService(client=client).list_daily_log_headers(456)

        client.get_all.assert_called_once_with(
            "/rest/v1.0/projects/456/daily_log_headers",
            params=None,
            headers={"Procore-Company-Id": "321"},
        )

    def test_headers_use_v10_path_and_date_filters(self) -> None:
        """Header listing uses v1.0 path and date filters."""
        client = Mock()
        client.get_all.return_value = {"data": [{"id": 9, "log_date": "2026-07-10"}]}

        result = DailyLogsService(client=client).list_daily_log_headers(
            456,
            company_id=123,
            start_date="2026-07-01",
            end_date="2026-07-10",
        )

        self.assertEqual(result[0].id, 9)
        client.get_all.assert_called_once_with(
            "/rest/v1.0/projects/456/daily_log_headers",
            params={"start_date": "2026-07-01", "end_date": "2026-07-10"},
            headers={"Procore-Company-Id": "123"},
        )

    def test_get_header_matches_id_or_date_locally(self) -> None:
        """Header retrieval lists and matches locally."""
        client = Mock()
        client.get_all.return_value = [
            {"id": 9, "log_date": "2026-07-09"},
            {"id": 10, "log_date": "2026-07-10"},
        ]
        service = DailyLogsService(client=client)

        self.assertEqual(service.get_daily_log_header(456, header_id=10, company_id=123).id, 10)
        self.assertEqual(
            service.get_daily_log_header(456, log_date="2026-07-09", company_id=123).id,
            9,
        )
        with self.assertRaises(ValidationError):
            service.get_daily_log_header(456, company_id=123)

    def test_list_daily_logs_maps_type_and_pagination(self) -> None:
        """Generic log listing maps known types to endpoints."""
        client = Mock()
        client.get_all.return_value = [{"id": 1, "comments": "Crew on site"}]

        result = DailyLogsService(client=client).list_daily_logs(
            456,
            "manpower",
            company_id=123,
            log_date="2026-07-10",
            page=2,
            per_page=100,
        )

        self.assertEqual(result[0].log_type, "manpower")
        client.get_all.assert_called_once_with(
            "/rest/v1.0/projects/456/manpower_logs",
            params={"log_date": "2026-07-10", "page": 2, "per_page": 100},
            headers={"Procore-Company-Id": "123"},
        )

    def test_invalid_log_type_raises_validation_error(self) -> None:
        """Unsupported log types fail before the API call."""
        with self.assertRaisesRegex(ValidationError, "Unsupported daily log type"):
            DailyLogsService(client=Mock()).list_daily_logs(456, "weather", company_id=123)

    def test_get_daily_log_matches_id_locally(self) -> None:
        """Single log retrieval lists and matches locally."""
        client = Mock()
        client.get_all.return_value = [{"id": 1}, {"id": 2}]

        result = DailyLogsService(client=client).get_daily_log(
            456,
            "notes",
            2,
            company_id=123,
        )

        self.assertEqual(result.id, 2)
        with self.assertRaises(NotFoundError):
            DailyLogsService(client=client).get_daily_log(456, "notes", 99, company_id=123)

    def test_delay_log_types_returns_models(self) -> None:
        """Delay log types use the verified nested endpoint."""
        client = Mock()
        client.get_all.return_value = [{"id": 1, "name": "Weather"}]

        result = DailyLogsService(client=client).list_delay_log_types(456, company_id=123)

        self.assertEqual(result[0].name, "Weather")
        client.get_all.assert_called_once_with(
            "/rest/v1.0/projects/456/daily_logs/delay_log_types",
            params=None,
            headers={"Procore-Company-Id": "123"},
        )

    def test_list_daily_logs_for_date_aggregates_types(self) -> None:
        """Aggregate helper collects selected log types for one date."""
        service = DailyLogsService(client=Mock())
        with patch.object(service, "list_daily_logs", side_effect=[["m"], ["n"]]) as helper:
            result = service.list_daily_logs_for_date(
                456,
                company_id=123,
                log_date="2026-07-10",
                log_types=["manpower", "notes"],
            )

        self.assertEqual(result.logs["manpower"], ["m"])
        self.assertEqual(result.logs["notes"], ["n"])
        self.assertEqual(helper.call_count, 2)

    def test_convenience_wrappers_delegate(self) -> None:
        """Convenience wrappers call generic log listing."""
        service = DailyLogsService(client=Mock())
        with patch.object(service, "list_daily_logs", return_value=["entry"]) as helper:
            self.assertEqual(service.list_manpower_logs(456, company_id=123), ["entry"])
            self.assertEqual(service.list_notes_logs(456, company_id=123), ["entry"])

        self.assertEqual(helper.call_args_list[0].args[:2], (456, "manpower"))
        self.assertEqual(helper.call_args_list[1].args[:2], (456, "notes"))

    def test_module_level_helpers_delegate_to_service(self) -> None:
        """Module-level helpers preserve the existing service style."""
        with patch("pyprocore.services.daily_logs.DailyLogsService") as service_cls:
            service = service_cls.return_value
            service.get_daily_log_counts.return_value = ["count"]
            service.list_daily_log_headers.return_value = ["header"]
            service.get_daily_log_header.return_value = "header"
            service.list_daily_logs.return_value = ["entry"]
            service.get_daily_log.return_value = "entry"
            service.list_delay_log_types.return_value = ["delay"]
            service.list_daily_logs_for_date.return_value = "summary"

            self.assertEqual(get_daily_log_counts(456), ["count"])
            self.assertEqual(list_daily_log_headers(456), ["header"])
            self.assertEqual(get_daily_log_header(456, header_id=1), "header")
            self.assertEqual(list_daily_logs(456, "manpower"), ["entry"])
            self.assertEqual(get_daily_log(456, "manpower", 1), "entry")
            self.assertEqual(list_delay_log_types(456), ["delay"])
            self.assertEqual(list_daily_logs_for_date(456), "summary")
            self.assertEqual(list_manpower_logs(456), ["entry"])
            self.assertEqual(list_notes_logs(456), ["entry"])


if __name__ == "__main__":
    unittest.main()
