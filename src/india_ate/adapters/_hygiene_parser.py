"""HTML/JSON snapshot parsing and strict field validation for HygieneRatingAdapter."""

import json
from datetime import date
from typing import Any, get_args

from bs4 import BeautifulSoup, Tag

from india_ate.models import IndiaFSSAI14, PremisesType

FSSAI_DIGITS = 14
VALID_PREMISES_TYPES: tuple[str, ...] = get_args(PremisesType)
_JSON_CONTAINER_KEYS = ("records", "data", "rows")


def clean_str(value: object) -> str:
    """Return stripped string if value is a str, else empty string."""
    return value.strip() if isinstance(value, str) else ""


def optional_str(value: object) -> str | None:
    """Return stripped non-empty string or None."""
    cleaned = clean_str(value)
    return cleaned if cleaned else None


def _dict_items(items: list[object]) -> list[dict[str, Any]]:
    return [dict(item) for item in items if isinstance(item, dict)]


def parse_json_bytes(raw: bytes) -> list[dict[str, Any]]:
    """Parse JSON snapshot bytes into candidate row dicts."""
    payload: object = json.loads(raw.decode("utf-8"))
    if isinstance(payload, list):
        return _dict_items(payload)
    if not isinstance(payload, dict):
        return []
    for key in _JSON_CONTAINER_KEYS:
        nested = payload.get(key)
        if isinstance(nested, list):
            return _dict_items(nested)
    return [dict(payload)]


def _extract_table_rows(table: Tag, headers: list[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for tr in table.find_all("tr"):
        cells = tr.find_all("td")
        if len(cells) != len(headers):
            continue
        rows.append(
            {
                headers[idx]: cells[idx].get_text(strip=True)
                for idx in range(len(headers))
            }
        )
    return rows


def parse_html_bytes(raw: bytes) -> list[dict[str, Any]]:
    """Parse HTML table bytes into candidate row dicts."""
    soup = BeautifulSoup(raw.decode("utf-8"), "html.parser")
    table = soup.find("table")
    if not isinstance(table, Tag):
        return []
    headers = [th.get_text(strip=True).lower() for th in table.find_all("th")]
    if not headers:
        return []
    return _extract_table_rows(table, headers)


def _validate_fssai_id(raw_fssai: str) -> str:
    if not raw_fssai:
        raise ValueError("Missing mandatory fssai_id")
    if not raw_fssai.isascii():
        raise ValueError("FSSAI ID must contain ASCII digits only")
    if len(raw_fssai) != FSSAI_DIGITS or not raw_fssai.isdigit():
        raise ValueError("FSSAI ID must be a 14-digit numeric string")
    IndiaFSSAI14(raw_value=raw_fssai).decode_offline()
    return raw_fssai


def _require_str(record: dict[str, Any], field: str) -> str:
    value = clean_str(record.get(field))
    if not value:
        raise ValueError(f"Missing mandatory {field}")
    return value


def _parse_audit_date(raw_date: object) -> date:
    try:
        return date.fromisoformat(clean_str(raw_date))
    except ValueError as exc:
        raise ValueError("Missing or invalid audit_date") from exc


def validate_record_fields(
    record: dict[str, Any],
) -> tuple[str, str, PremisesType, str, date]:
    """Validate mandatory Hygiene Rating record fields or raise ValueError."""
    fssai_id = _validate_fssai_id(clean_str(record.get("fssai_id")))
    legal_name = _require_str(record, "legal_name")
    rating = _require_str(record, "rating")
    audit_date = _parse_audit_date(record.get("audit_date"))
    raw_type = clean_str(record.get("premises_type")) or "restaurant"
    if raw_type not in VALID_PREMISES_TYPES:
        raise ValueError(f"Invalid premises_type: {raw_type!r}")
    premises_type: PremisesType = raw_type  # type: ignore[assignment]
    return fssai_id, legal_name, premises_type, rating, audit_date
