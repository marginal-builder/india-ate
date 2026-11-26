"""Shared deterministic parsing and validation helpers for adapters."""

from datetime import UTC, date, datetime
from typing import Any

from pydantic import HttpUrl

from india_ate.adapters._hygiene_parser import optional_str, parse_json_bytes
from india_ate.models import (
    EvidenceProvenance,
    FoodPremises,
    IndiaFSSAI14,
    PremisesType,
    QuarantinedRecord,
    VerificationTier,
)

VALID_PREMISES_TYPES: frozenset[str] = frozenset(
    {
        "cloud_kitchen",
        "dark_store",
        "restaurant",
        "co_packer_factory",
        "dairy_unit",
        "warehouse",
        "retail_vendor",
    }
)


def parse_json_records(raw: bytes) -> list[dict[str, Any]]:
    """Parse JSON list or wrapper dict into candidate row dictionaries."""
    return parse_json_bytes(raw)


def require_non_empty(record: dict[str, Any], key: str, label: str) -> str:
    """Return stripped non-empty string field or raise ValueError."""
    value = optional_str(record.get(key))
    if value is None:
        raise ValueError(f"Missing required field: {label}")
    return value


def validate_fssai_id(record: dict[str, Any]) -> str:
    """Extract and deterministically validate a 14-digit FSSAI ID."""
    raw = require_non_empty(record, "fssai_id", "fssai_id")
    IndiaFSSAI14(raw_value=raw).decode_offline()
    return raw


def parse_iso_date(record: dict[str, Any], key: str) -> date:
    """Parse an ISO YYYY-MM-DD date field or raise ValueError."""
    raw = require_non_empty(record, key, key)
    try:
        return date.fromisoformat(raw)
    except ValueError as exc:
        raise ValueError(f"Invalid ISO date for {key}: {raw}") from exc


def parse_iso_datetime(record: dict[str, Any], key: str, default: datetime) -> datetime:
    """Parse an ISO datetime field or fall back to default when omitted."""
    raw = optional_str(record.get(key))
    if raw is None:
        return default
    try:
        parsed = datetime.fromisoformat(raw)
        return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=UTC)
    except ValueError as exc:
        raise ValueError(f"Invalid ISO datetime for {key}: {raw}") from exc


def resolve_premises_type(
    record: dict[str, Any], default: PremisesType = "restaurant"
) -> PremisesType:
    """Return validated PremisesType or default when omitted."""
    raw = optional_str(record.get("premises_type"))
    if raw is None:
        return default
    if raw not in VALID_PREMISES_TYPES:
        raise ValueError(f"Unsupported premises_type: {raw}")
    return raw  # type: ignore[return-value]


def build_provenance(
    source_name: str,
    source_url: str,
    retrieved_at: datetime,
    content_sha256: str,
    tier: VerificationTier = "official_registry",
) -> EvidenceProvenance:
    """Construct an immutable EvidenceProvenance record."""
    return EvidenceProvenance(
        source_name=source_name,
        source_url=HttpUrl(source_url),
        retrieved_at=retrieved_at,
        content_sha256=content_sha256,
        verification_tier=tier,
    )


def build_fssai_premises(
    record: dict[str, Any],
    fssai_id: str,
    legal_name: str,
    premises_type: PremisesType,
    provenance: EvidenceProvenance,
) -> FoodPremises:
    """Construct a FoodPremises entity keyed by canonical FSSAI URI."""
    return FoodPremises(
        entity_id=f"actor:in:fssai:{fssai_id}",
        legal_name=legal_name,
        jurisdiction_iso="IN",
        regulatory_ids=[IndiaFSSAI14(raw_value=fssai_id)],
        provenance=[provenance],
        premises_type=premises_type,
        address=optional_str(record.get("address")),
        postal_code=optional_str(record.get("postal_code")),
        city=optional_str(record.get("city")),
        state=optional_str(record.get("state")),
    )


def make_quarantined(
    source_name: str,
    record: dict[str, Any],
    reason: str,
    quarantined_at: datetime,
) -> QuarantinedRecord:
    """Construct a QuarantinedRecord for an invalid or ambiguous row."""
    return QuarantinedRecord(
        source_name=source_name,
        raw_record=dict(record),
        reason=reason,
        quarantined_at=quarantined_at,
    )
