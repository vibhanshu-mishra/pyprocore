"""Daily Logs services for the Procore SDK."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from pyprocore.core import endpoints
from pyprocore.core.client import ProcoreClient
from pyprocore.core.config import get_settings
from pyprocore.core.exceptions import NotFoundError, ValidationError
from pyprocore.models import (
    DailyLogCount,
    DailyLogEntry,
    DailyLogHeader,
    DailyLogsByType,
    DelayLogType,
)
from pyprocore.services.query_params import build_query_params

DAILY_LOG_TYPES = tuple(endpoints.DAILY_LOG_TYPES.keys())
DAILY_LOG_PATHS = dict(endpoints.DAILY_LOG_TYPES)


class DailyLogsService:
    """Service for read-only Procore Daily Logs resources."""

    def __init__(self, client: ProcoreClient | None = None) -> None:
        """Initialize the service.

        Args:
            client: Optional shared Procore HTTP client.
        """
        self._client = client or ProcoreClient()

    def get_daily_log_counts(
        self,
        project_id: int,
        company_id: int | None = None,
        log_date: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[DailyLogCount]:
        """Return Daily Log counts for a project."""
        resolved_company_id = self._resolve_company_id(company_id)
        self._validate_positive_id(project_id, "project_id")
        response = self._client.get(
            endpoints.daily_log_counts(project_id),
            params=self._date_params(
                params=params,
                extra_params=extra_params,
                log_date=log_date,
                start_date=start_date,
                end_date=end_date,
            ),
            headers=self._company_headers(resolved_company_id),
        )
        return [DailyLogCount.model_validate(item) for item in self._count_items(response)]

    def list_daily_log_headers(
        self,
        project_id: int,
        company_id: int | None = None,
        log_date: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[DailyLogHeader]:
        """Return Daily Log headers for a project."""
        resolved_company_id = self._resolve_company_id(company_id)
        self._validate_positive_id(project_id, "project_id")
        response = self._client.get_all(
            endpoints.daily_log_headers(project_id),
            params=self._date_params(
                params=params,
                extra_params=extra_params,
                log_date=log_date,
                start_date=start_date,
                end_date=end_date,
            ),
            headers=self._company_headers(resolved_company_id),
        )
        return [DailyLogHeader.model_validate(item) for item in self._extract_items(response)]

    def get_daily_log_header(
        self,
        project_id: int,
        header_id: int | None = None,
        log_date: str | None = None,
        company_id: int | None = None,
    ) -> DailyLogHeader:
        """Return one Daily Log header by local lookup.

        A direct show endpoint is not confirmed for this phase, so the SDK
        lists headers and matches by ID or date locally.
        """
        if header_id is None and log_date is None:
            raise ValidationError("Provide header_id or log_date to get a Daily Log header.")
        self._validate_optional_id(header_id, "header_id")
        headers = self.list_daily_log_headers(project_id, company_id=company_id, log_date=log_date)
        for header in headers:
            if header_id is not None and header.id == header_id:
                return header
            if log_date is not None and log_date in {header.log_date, header.date}:
                return header
        raise NotFoundError("No Daily Log header matched the provided criteria.")

    def list_daily_logs(
        self,
        project_id: int,
        log_type: str,
        company_id: int | None = None,
        log_date: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        page: int | None = None,
        per_page: int | None = None,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[DailyLogEntry]:
        """Return Daily Log entries for a supported log type."""
        resolved_company_id = self._resolve_company_id(company_id)
        self._validate_positive_id(project_id, "project_id")
        normalized_type = self._normalize_log_type(log_type)
        self._validate_optional_id(page, "page")
        self._validate_optional_id(per_page, "per_page")
        response = self._client.get_all(
            endpoints.daily_log_type(project_id, normalized_type),
            params=self._date_params(
                params=params,
                extra_params=extra_params,
                log_date=log_date,
                start_date=start_date,
                end_date=end_date,
                page=page,
                per_page=per_page,
            ),
            headers=self._company_headers(resolved_company_id),
        )
        entries = [DailyLogEntry.model_validate(item) for item in self._extract_items(response)]
        for entry in entries:
            entry.log_type = entry.log_type or normalized_type
        return entries

    def get_daily_log(
        self,
        project_id: int,
        log_type: str,
        log_id: int,
        company_id: int | None = None,
        log_date: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> DailyLogEntry:
        """Return one Daily Log entry by listing and matching locally."""
        self._validate_positive_id(log_id, "log_id")
        for entry in self.list_daily_logs(
            project_id,
            log_type,
            company_id=company_id,
            log_date=log_date,
            start_date=start_date,
            end_date=end_date,
            params=params,
            **extra_params,
        ):
            if entry.id == log_id:
                return entry
        raise NotFoundError(f"Daily Log entry {log_id} was not found for log type {log_type!r}.")

    def list_delay_log_types(
        self,
        project_id: int,
        company_id: int | None = None,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[DelayLogType]:
        """Return configured delay log types for a project."""
        resolved_company_id = self._resolve_company_id(company_id)
        self._validate_positive_id(project_id, "project_id")
        response = self._client.get_all(
            endpoints.delay_log_types(project_id),
            params=build_query_params(params=params, extra_params=extra_params),
            headers=self._company_headers(resolved_company_id),
        )
        return [DelayLogType.model_validate(item) for item in self._extract_items(response)]

    def list_daily_logs_for_date(
        self,
        project_id: int,
        company_id: int | None = None,
        log_date: str | None = None,
        log_types: Sequence[str] | None = None,
    ) -> DailyLogsByType:
        """Return multiple Daily Log types for one date."""
        selected_types = list(log_types or DAILY_LOG_TYPES)
        summary = DailyLogsByType(project_id=project_id, log_date=log_date)
        for log_type in selected_types:
            normalized_type = self._normalize_log_type(log_type)
            try:
                summary.logs[normalized_type] = self.list_daily_logs(
                    project_id,
                    normalized_type,
                    company_id=company_id,
                    log_date=log_date,
                )
            except Exception as exc:
                summary.errors[normalized_type] = str(exc)
        return summary

    def list_manpower_logs(
        self, project_id: int, company_id: int | None = None, **filters: Any
    ) -> list[DailyLogEntry]:
        """Return manpower logs."""
        return self.list_daily_logs(project_id, "manpower", company_id=company_id, **filters)

    def list_notes_logs(
        self, project_id: int, company_id: int | None = None, **filters: Any
    ) -> list[DailyLogEntry]:
        """Return notes logs."""
        return self.list_daily_logs(project_id, "notes", company_id=company_id, **filters)

    def list_daily_construction_report_logs(
        self, project_id: int, company_id: int | None = None, **filters: Any
    ) -> list[DailyLogEntry]:
        """Return daily construction report logs."""
        return self.list_daily_logs(
            project_id, "daily_construction_report", company_id=company_id, **filters
        )

    def list_delay_logs(
        self, project_id: int, company_id: int | None = None, **filters: Any
    ) -> list[DailyLogEntry]:
        """Return delay logs."""
        return self.list_daily_logs(project_id, "delay", company_id=company_id, **filters)

    def list_delivery_logs(
        self, project_id: int, company_id: int | None = None, **filters: Any
    ) -> list[DailyLogEntry]:
        """Return delivery logs."""
        return self.list_daily_logs(project_id, "delivery", company_id=company_id, **filters)

    def list_call_logs(
        self, project_id: int, company_id: int | None = None, **filters: Any
    ) -> list[DailyLogEntry]:
        """Return call logs."""
        return self.list_daily_logs(project_id, "call", company_id=company_id, **filters)

    def list_accident_logs(
        self, project_id: int, company_id: int | None = None, **filters: Any
    ) -> list[DailyLogEntry]:
        """Return accident logs."""
        return self.list_daily_logs(project_id, "accident", company_id=company_id, **filters)

    def list_dumpster_logs(
        self, project_id: int, company_id: int | None = None, **filters: Any
    ) -> list[DailyLogEntry]:
        """Return dumpster logs."""
        return self.list_daily_logs(project_id, "dumpster", company_id=company_id, **filters)

    def list_visitor_logs(
        self, project_id: int, company_id: int | None = None, **filters: Any
    ) -> list[DailyLogEntry]:
        """Return visitor logs."""
        return self.list_daily_logs(project_id, "visitor", company_id=company_id, **filters)

    def list_productivity_logs(
        self, project_id: int, company_id: int | None = None, **filters: Any
    ) -> list[DailyLogEntry]:
        """Return productivity logs."""
        return self.list_daily_logs(project_id, "productivity", company_id=company_id, **filters)

    def list_plan_revision_logs(
        self, project_id: int, company_id: int | None = None, **filters: Any
    ) -> list[DailyLogEntry]:
        """Return plan revision logs."""
        return self.list_daily_logs(project_id, "plan_revision", company_id=company_id, **filters)

    @staticmethod
    def _resolve_company_id(company_id: int | None) -> int:
        """Return an explicit or configured company ID."""
        resolved_company_id = company_id or get_settings().company_id
        DailyLogsService._validate_positive_id(resolved_company_id, "company_id")
        return resolved_company_id

    @staticmethod
    def _company_headers(company_id: int) -> dict[str, str]:
        """Return required company headers for Daily Logs endpoints."""
        return {"Procore-Company-Id": str(company_id)}

    @staticmethod
    def _date_params(
        *,
        params: Mapping[str, Any] | None,
        extra_params: Mapping[str, Any],
        log_date: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        page: int | None = None,
        per_page: int | None = None,
    ) -> dict[str, Any] | None:
        """Build shared Daily Logs query parameters."""
        return build_query_params(
            params=params,
            extra_params=extra_params,
            log_date=log_date,
            start_date=start_date,
            end_date=end_date,
            page=page,
            per_page=per_page,
        )

    @classmethod
    def _extract_items(cls, payload: object) -> list[Mapping[str, Any]]:
        """Extract collection items from direct or envelope responses."""
        if isinstance(payload, list):
            items: list[Mapping[str, Any]] = []
            for item in payload:
                if isinstance(item, Mapping):
                    data = item.get("data")
                    if isinstance(data, list):
                        items.extend(cls._ensure_mapping(value) for value in data)
                    else:
                        items.append(item)
                    continue
                raise ValidationError("Expected Daily Logs item to be an object.")
            return items
        if isinstance(payload, Mapping):
            for key in ("data", "items", "results", "daily_logs"):
                value = payload.get(key)
                if isinstance(value, list):
                    return [cls._ensure_mapping(item) for item in value]
            return [payload]
        raise ValidationError("Expected Daily Logs response to be a list or object.")

    @classmethod
    def _count_items(cls, payload: object) -> list[Mapping[str, Any]]:
        """Extract count items from list, envelope, or mapping count responses."""
        if isinstance(payload, Mapping) and not any(
            isinstance(payload.get(key), list) for key in ("data", "items", "results")
        ):
            return [
                {"log_type": key, "count": value}
                for key, value in payload.items()
                if isinstance(value, int)
            ] or [payload]
        return cls._extract_items(payload)

    @staticmethod
    def _ensure_mapping(item: object) -> Mapping[str, Any]:
        """Validate that a payload item is a mapping."""
        if not isinstance(item, Mapping):
            raise ValidationError("Expected Daily Logs item to be an object.")
        return item

    @staticmethod
    def _normalize_log_type(log_type: str) -> str:
        """Normalize and validate a Daily Logs type."""
        normalized = log_type.strip().casefold().replace("-", "_")
        if normalized not in DAILY_LOG_PATHS:
            supported = ", ".join(DAILY_LOG_TYPES)
            raise ValidationError(
                f"Unsupported daily log type {log_type!r}. Supported types: {supported}."
            )
        return normalized

    @classmethod
    def _validate_optional_id(cls, value: int | None, name: str) -> None:
        """Validate optional Procore integer identifiers."""
        if value is not None:
            cls._validate_positive_id(value, name)

    @staticmethod
    def _validate_positive_id(value: int, name: str) -> None:
        """Validate Procore integer identifiers."""
        if value <= 0:
            raise ValidationError(f"{name} must be a positive integer.")


def get_daily_log_counts(
    project_id: int,
    company_id: int | None = None,
    client: ProcoreClient | None = None,
    **filters: Any,
) -> list[DailyLogCount]:
    """Return Daily Log counts for a project."""
    return DailyLogsService(client=client).get_daily_log_counts(
        project_id, company_id=company_id, **filters
    )


def list_daily_log_headers(
    project_id: int,
    company_id: int | None = None,
    client: ProcoreClient | None = None,
    **filters: Any,
) -> list[DailyLogHeader]:
    """Return Daily Log headers for a project."""
    return DailyLogsService(client=client).list_daily_log_headers(
        project_id, company_id=company_id, **filters
    )


def get_daily_log_header(
    project_id: int,
    header_id: int | None = None,
    log_date: str | None = None,
    company_id: int | None = None,
    client: ProcoreClient | None = None,
) -> DailyLogHeader:
    """Return one Daily Log header by local lookup."""
    return DailyLogsService(client=client).get_daily_log_header(
        project_id, header_id=header_id, log_date=log_date, company_id=company_id
    )


def list_daily_logs(
    project_id: int,
    log_type: str,
    company_id: int | None = None,
    client: ProcoreClient | None = None,
    **filters: Any,
) -> list[DailyLogEntry]:
    """Return Daily Logs for a supported type."""
    return DailyLogsService(client=client).list_daily_logs(
        project_id, log_type, company_id=company_id, **filters
    )


def get_daily_log(
    project_id: int,
    log_type: str,
    log_id: int,
    company_id: int | None = None,
    client: ProcoreClient | None = None,
    **filters: Any,
) -> DailyLogEntry:
    """Return one Daily Log by local lookup."""
    return DailyLogsService(client=client).get_daily_log(
        project_id, log_type, log_id, company_id=company_id, **filters
    )


def list_delay_log_types(
    project_id: int,
    company_id: int | None = None,
    client: ProcoreClient | None = None,
    **filters: Any,
) -> list[DelayLogType]:
    """Return delay log types for a project."""
    return DailyLogsService(client=client).list_delay_log_types(
        project_id, company_id=company_id, **filters
    )


def list_daily_logs_for_date(
    project_id: int,
    company_id: int | None = None,
    log_date: str | None = None,
    log_types: Sequence[str] | None = None,
    client: ProcoreClient | None = None,
) -> DailyLogsByType:
    """Return multiple Daily Log types for one date."""
    return DailyLogsService(client=client).list_daily_logs_for_date(
        project_id, company_id=company_id, log_date=log_date, log_types=log_types
    )


def list_manpower_logs(
    project_id: int,
    company_id: int | None = None,
    client: ProcoreClient | None = None,
    **filters: Any,
) -> list[DailyLogEntry]:
    """Return manpower logs."""
    return list_daily_logs(project_id, "manpower", company_id=company_id, client=client, **filters)


def list_notes_logs(
    project_id: int,
    company_id: int | None = None,
    client: ProcoreClient | None = None,
    **filters: Any,
) -> list[DailyLogEntry]:
    """Return notes logs."""
    return list_daily_logs(project_id, "notes", company_id=company_id, client=client, **filters)


def list_daily_construction_report_logs(
    project_id: int,
    company_id: int | None = None,
    client: ProcoreClient | None = None,
    **filters: Any,
) -> list[DailyLogEntry]:
    """Return daily construction report logs."""
    return list_daily_logs(
        project_id, "daily_construction_report", company_id=company_id, client=client, **filters
    )


def list_delay_logs(
    project_id: int,
    company_id: int | None = None,
    client: ProcoreClient | None = None,
    **filters: Any,
) -> list[DailyLogEntry]:
    """Return delay logs."""
    return list_daily_logs(project_id, "delay", company_id=company_id, client=client, **filters)


def list_delivery_logs(
    project_id: int,
    company_id: int | None = None,
    client: ProcoreClient | None = None,
    **filters: Any,
) -> list[DailyLogEntry]:
    """Return delivery logs."""
    return list_daily_logs(project_id, "delivery", company_id=company_id, client=client, **filters)


def list_call_logs(
    project_id: int,
    company_id: int | None = None,
    client: ProcoreClient | None = None,
    **filters: Any,
) -> list[DailyLogEntry]:
    """Return call logs."""
    return list_daily_logs(project_id, "call", company_id=company_id, client=client, **filters)


def list_accident_logs(
    project_id: int,
    company_id: int | None = None,
    client: ProcoreClient | None = None,
    **filters: Any,
) -> list[DailyLogEntry]:
    """Return accident logs."""
    return list_daily_logs(project_id, "accident", company_id=company_id, client=client, **filters)


def list_dumpster_logs(
    project_id: int,
    company_id: int | None = None,
    client: ProcoreClient | None = None,
    **filters: Any,
) -> list[DailyLogEntry]:
    """Return dumpster logs."""
    return list_daily_logs(project_id, "dumpster", company_id=company_id, client=client, **filters)


def list_visitor_logs(
    project_id: int,
    company_id: int | None = None,
    client: ProcoreClient | None = None,
    **filters: Any,
) -> list[DailyLogEntry]:
    """Return visitor logs."""
    return list_daily_logs(project_id, "visitor", company_id=company_id, client=client, **filters)


def list_productivity_logs(
    project_id: int,
    company_id: int | None = None,
    client: ProcoreClient | None = None,
    **filters: Any,
) -> list[DailyLogEntry]:
    """Return productivity logs."""
    return list_daily_logs(
        project_id, "productivity", company_id=company_id, client=client, **filters
    )


def list_plan_revision_logs(
    project_id: int,
    company_id: int | None = None,
    client: ProcoreClient | None = None,
    **filters: Any,
) -> list[DailyLogEntry]:
    """Return plan revision logs."""
    return list_daily_logs(
        project_id, "plan_revision", company_id=company_id, client=client, **filters
    )
