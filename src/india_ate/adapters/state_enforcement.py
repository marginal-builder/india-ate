"""Pluggable State Enforcement adapter (e.g. TG SAFE, Maharashtra FDA)."""

import hashlib
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel

from india_ate.adapters import BaseSourceAdapter
from india_ate.adapters._common import (
    build_fssai_premises,
    build_provenance,
    make_quarantined,
    parse_iso_date,
    parse_json_records,
    require_non_empty,
    resolve_premises_type,
    validate_fssai_id,
)
from india_ate.adapters.http import HttpFetcher, HttpxFetcher
from india_ate.models import AuthoritativeEvent, IngestionBatch, QuarantinedRecord

DEFAULT_ENFORCEMENT_URL = "https://tgsafe.telangana.gov.in/enforcement/snapshot"


class StateEnforcementAdapter(BaseSourceAdapter):
    """Pluggable adapter for state food-safety raids & licence suspensions."""

    jurisdiction_iso = "IN"

    def __init__(
        self,
        source_name: str = "Telangana TG SAFE",
        portal_url: str = DEFAULT_ENFORCEMENT_URL,
        fetcher: HttpFetcher | None = None,
    ) -> None:
        self.source_name = source_name
        self.portal_url = portal_url
        self._fetcher: HttpFetcher = fetcher or HttpxFetcher()
        self._content_sha256 = hashlib.sha256(b"").hexdigest()
        self._retrieved_at = datetime.now(UTC)

    def fetch(self) -> bytes:
        """Fetch raw enforcement snapshot bytes via the injected HttpFetcher."""
        raw = self._fetcher.get(self.portal_url)
        self._content_sha256 = hashlib.sha256(raw).hexdigest()
        self._retrieved_at = datetime.now(UTC)
        return raw

    def parse(self, raw: bytes) -> list[dict[str, Any]]:
        """Parse raw JSON bytes into candidate enforcement dictionaries."""
        self._content_sha256 = hashlib.sha256(raw).hexdigest()
        self._retrieved_at = datetime.now(UTC)
        return parse_json_records(raw)

    def _emit_one(self, record: dict[str, Any]) -> tuple[BaseModel, AuthoritativeEvent]:
        fssai_id = validate_fssai_id(record)
        legal_name = require_non_empty(record, "legal_name", "legal_name")
        event_date = parse_iso_date(record, "event_date")
        ptype = resolve_premises_type(record, default="cloud_kitchen")
        prov = build_provenance(
            self.source_name, self.portal_url, self._retrieved_at, self._content_sha256
        )
        premises = build_fssai_premises(record, fssai_id, legal_name, ptype, prov)
        slug = self.source_name.lower().replace(" ", "_")
        event = AuthoritativeEvent(
            event_id=f"evt:enf:{slug}:{fssai_id}:{event_date.isoformat()}",
            event_type="enforcement_raid_or_suspension",
            target_entity_id=premises.entity_id,
            jurisdiction_iso=self.jurisdiction_iso,
            event_date=event_date,
            status=require_non_empty(record, "status", "status"),
            verbatim_summary=require_non_empty(
                record, "verbatim_summary", "verbatim_summary"
            ),
            provenance=prov,
        )
        return premises, event

    def validate_and_emit_batch(self, records: list[dict[str, Any]]) -> IngestionBatch:
        """Validate enforcement records strictly and quarantine invalid rows."""
        entities: list[BaseModel] = []
        quarantined: list[QuarantinedRecord] = []
        for record in records:
            try:
                premises, event = self._emit_one(record)
            except ValueError as exc:
                quarantined.append(
                    make_quarantined(
                        self.source_name, record, str(exc), self._retrieved_at
                    )
                )
                continue
            entities.extend([premises, event])
        return IngestionBatch(entities=entities, quarantined=quarantined)

    def validate_and_emit(self, records: list[dict[str, Any]]) -> list[BaseModel]:
        """Return only validated entities, routing invalid rows to quarantine."""
        return self.validate_and_emit_batch(records).entities
