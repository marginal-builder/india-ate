"""FSSAI Hygiene Rating Portal adapter with HTML/JSON parsing and quarantine."""

import hashlib
from datetime import UTC, date, datetime
from typing import Any

from pydantic import BaseModel, HttpUrl

from india_ate.adapters import BaseSourceAdapter
from india_ate.adapters._hygiene_parser import (
    optional_str,
    parse_html_bytes,
    parse_json_bytes,
    validate_record_fields,
)
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
        if raw.lstrip().startswith((b"{", b"[")):
            return parse_json_bytes(raw)
        return parse_html_bytes(raw)

    def _build_provenance(self) -> EvidenceProvenance:
        return EvidenceProvenance(
            source_name=self.source_name,
            source_url=HttpUrl(self.portal_url),
            retrieved_at=self._retrieved_at,
            content_sha256=self._content_sha256,
            verification_tier="official_registry",
        )

    def _build_premises(
        self,
        record: dict[str, Any],
        fssai_id: str,
        legal_name: str,
        premises_type: PremisesType,
        provenance: EvidenceProvenance,
    ) -> FoodPremises:
        return FoodPremises(
            entity_id=f"actor:in:fssai:{fssai_id}",
            legal_name=legal_name,
            jurisdiction_iso=self.jurisdiction_iso,
            regulatory_ids=[IndiaFSSAI14(raw_value=fssai_id)],
            provenance=[provenance],
            premises_type=premises_type,
            address=optional_str(record.get("address")),
            postal_code=optional_str(record.get("postal_code")),
            city=optional_str(record.get("city")),
            state=optional_str(record.get("state")),
        )

    def _build_event(
        self,
        fssai_id: str,
        rating: str,
        audit_date: date,
        provenance: EvidenceProvenance,
    ) -> AuthoritativeEvent:
        return AuthoritativeEvent(
            event_id=f"evt:hygiene:{fssai_id}:{audit_date.isoformat()}",
            event_type="hygiene_audit",
            target_entity_id=f"actor:in:fssai:{fssai_id}",
            jurisdiction_iso=self.jurisdiction_iso,
            event_date=audit_date,
            status=rating,
            verbatim_summary=(
                f"FSSAI Hygiene Rating {rating} audited on {audit_date.isoformat()}"
            ),
            provenance=provenance,
        )

    def _quarantine_record(
        self, record: dict[str, Any], reason: str
    ) -> QuarantinedRecord:
        return QuarantinedRecord(
            source_name=self.source_name,
            raw_record=dict(record),
            reason=reason,
            quarantined_at=self._retrieved_at,
        )

    def validate_and_emit_batch(self, records: list[dict[str, Any]]) -> IngestionBatch:
        """Validate candidate rows strictly and quarantine invalid rows."""
        entities: list[BaseModel] = []
        quarantined: list[QuarantinedRecord] = []
        provenance = self._build_provenance()
        for record in records:
            try:
                fssai_id, legal_name, ptype, rating, audit_date = (
                    validate_record_fields(record)
                )
            except ValueError as exc:
                quarantined.append(self._quarantine_record(record, str(exc)))
                continue
            entities.append(
                self._build_premises(record, fssai_id, legal_name, ptype, provenance)
            )
            entities.append(self._build_event(fssai_id, rating, audit_date, provenance))
        return IngestionBatch(entities=entities, quarantined=quarantined)

    def validate_and_emit(self, records: list[dict[str, Any]]) -> list[BaseModel]:
        """Return only validated entities, routing invalid rows to quarantine."""
        return self.validate_and_emit_batch(records).entities
