"""FSSAI Hygiene Rating Portal adapter with HTML/JSON parsing and quarantine."""

import hashlib
import json
from datetime import UTC, date, datetime
from typing import Any, get_args

from bs4 import BeautifulSoup
from pydantic import BaseModel, HttpUrl

from india_ate.adapters import BaseSourceAdapter
from india_ate.adapters.http import HttpFetcher, HttpxFetcher
from india_ate.models import (
    AuthoritativeEvent,
    EvidenceProvenance,
    FoodPremises,
    IndiaFSSAI14,
    IngestionBatch,
    PremisesType,
    QuarantinedRecord,
)

DEFAULT_HYGIENE_URL = "https://hygiene.fssai.gov.in/snapshot"
FSSAI_DIGITS = 14
VALID_PREMISES_TYPES: tuple[str, ...] = get_args(PremisesType)


def _clean_str(value: object) -> str:
    return value.strip() if isinstance(value, str) else ""


def _optional_str(value: object) -> str | None:
    cleaned = _clean_str(value)
    return cleaned if cleaned else None


def _parse_json_bytes(raw: bytes) -> list[dict[str, Any]]:
    payload: object = json.loads(raw.decode("utf-8"))
    if isinstance(payload, list):
        return [dict(item) for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        for key in ("records", "data", "rows"):
            nested = payload.get(key)
            if isinstance(nested, list):
                return [dict(item) for item in nested if isinstance(item, dict)]
        return [dict(payload)]
    return []


def _parse_html_bytes(raw: bytes) -> list[dict[str, Any]]:
    soup = BeautifulSoup(raw.decode("utf-8"), "html.parser")
    table = soup.find("table")
    if table is None:
        return []
    headers = [th.get_text(strip=True).lower() for th in table.find_all("th")]
    if not headers:
        return []
    rows: list[dict[str, Any]] = []
    for tr in table.find_all("tr"):
        cells = tr.find_all("td")
        if len(cells) != len(headers):
            continue
        row = {
            headers[idx]: cells[idx].get_text(strip=True) for idx in range(len(headers))
        }
        rows.append(row)
    return rows


def _validate_fssai_id(raw_fssai: str) -> str:
    if not raw_fssai:
        raise ValueError("Missing mandatory fssai_id")
    if not raw_fssai.isascii():
        raise ValueError("FSSAI ID must contain ASCII digits only")
    if len(raw_fssai) != FSSAI_DIGITS or not raw_fssai.isdigit():
        raise ValueError("FSSAI ID must be a 14-digit numeric string")
    IndiaFSSAI14(raw_value=raw_fssai).decode_offline()
    return raw_fssai


def _validate_record_fields(
    record: dict[str, Any],
) -> tuple[str, str, PremisesType, str, date]:
    fssai_id = _validate_fssai_id(_clean_str(record.get("fssai_id")))
    legal_name = _clean_str(record.get("legal_name"))
    if not legal_name:
        raise ValueError("Missing mandatory legal_name")
    rating = _clean_str(record.get("rating"))
    if not rating:
        raise ValueError("Missing mandatory rating")
    audit_date_str = _clean_str(record.get("audit_date"))
    try:
        audit_date = date.fromisoformat(audit_date_str)
    except ValueError as exc:
        raise ValueError("Missing or invalid audit_date") from exc
    raw_type = _clean_str(record.get("premises_type")) or "restaurant"
    if raw_type not in VALID_PREMISES_TYPES:
        raise ValueError(f"Invalid premises_type: {raw_type!r}")
    premises_type: PremisesType = raw_type  # type: ignore[assignment]
    return fssai_id, legal_name, premises_type, rating, audit_date


class HygieneRatingAdapter(BaseSourceAdapter):
    """Adapter for FSSAI Hygiene Rating HTML/JSON snapshots and live portal."""

    source_name = "FSSAI Hygiene Rating Portal"
    jurisdiction_iso = "IN"

    def __init__(
        self,
        fetcher: HttpFetcher | None = None,
        portal_url: str = DEFAULT_HYGIENE_URL,
        state_code: str | None = None,
    ) -> None:
        self._fetcher: HttpFetcher = fetcher or HttpxFetcher()
        self.portal_url = portal_url
        self.state_code = state_code
        self._content_sha256: str = hashlib.sha256(b"").hexdigest()
        self._retrieved_at: datetime = datetime.now(UTC)

    def fetch(self) -> bytes:
        """Fetch raw HTML or JSON snapshot bytes via the injected HttpFetcher."""
        params = {"state": self.state_code} if self.state_code else None
        raw = self._fetcher.get(self.portal_url, params=params)
        self._content_sha256 = hashlib.sha256(raw).hexdigest()
        self._retrieved_at = datetime.now(UTC)
        return raw

    def parse(self, raw: bytes) -> list[dict[str, Any]]:
        """Parse raw HTML or JSON snapshot bytes into candidate row dicts."""
        self._content_sha256 = hashlib.sha256(raw).hexdigest()
        self._retrieved_at = datetime.now(UTC)
        stripped = raw.lstrip()
        if stripped.startswith((b"{", b"[")):
            return _parse_json_bytes(raw)
        return _parse_html_bytes(raw)

    def _build_entities(
        self,
        record: dict[str, Any],
        fssai_id: str,
        legal_name: str,
        premises_type: PremisesType,
        rating: str,
        audit_date: date,
    ) -> tuple[FoodPremises, AuthoritativeEvent]:
        provenance = EvidenceProvenance(
            source_name=self.source_name,
            source_url=HttpUrl(self.portal_url),
            retrieved_at=self._retrieved_at,
            content_sha256=self._content_sha256,
            verification_tier="official_registry",
        )
        entity_id = f"actor:in:fssai:{fssai_id}"
        premises = FoodPremises(
            entity_id=entity_id,
            legal_name=legal_name,
            jurisdiction_iso=self.jurisdiction_iso,
            regulatory_ids=[IndiaFSSAI14(raw_value=fssai_id)],
            provenance=[provenance],
            premises_type=premises_type,
            address=_optional_str(record.get("address")),
            postal_code=_optional_str(record.get("postal_code")),
            city=_optional_str(record.get("city")),
            state=_optional_str(record.get("state")),
        )
        event = AuthoritativeEvent(
            event_id=f"evt:hygiene:{fssai_id}:{audit_date.isoformat()}",
            event_type="hygiene_audit",
            target_entity_id=entity_id,
            jurisdiction_iso=self.jurisdiction_iso,
            event_date=audit_date,
            status=rating,
            verbatim_summary=(
                f"FSSAI Hygiene Rating {rating} audited on {audit_date.isoformat()}"
            ),
            provenance=provenance,
        )
        return premises, event

    def validate_and_emit_batch(self, records: list[dict[str, Any]]) -> IngestionBatch:
        """Validate candidate rows strictly and quarantine invalid rows."""
        entities: list[BaseModel] = []
        quarantined: list[QuarantinedRecord] = []
        for record in records:
            try:
                fssai_id, legal_name, ptype, rating, audit_date = (
                    _validate_record_fields(record)
                )
            except ValueError as exc:
                quarantined.append(
                    QuarantinedRecord(
                        source_name=self.source_name,
                        raw_record=dict(record),
                        reason=str(exc),
                        quarantined_at=self._retrieved_at,
                    )
                )
                continue
            premises, event = self._build_entities(
                record, fssai_id, legal_name, ptype, rating, audit_date
            )
            entities.extend([premises, event])
        return IngestionBatch(entities=entities, quarantined=quarantined)

    def validate_and_emit(self, records: list[dict[str, Any]]) -> list[BaseModel]:
        """Return only validated entities, routing invalid rows to quarantine."""
        return self.validate_and_emit_batch(records).entities
