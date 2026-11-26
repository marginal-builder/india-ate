"""ONDC Open Catalog adapter mapping BrandListing -> FoodPremises."""

import hashlib
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel

from india_ate.adapters import BaseSourceAdapter
from india_ate.adapters._common import (
    build_fssai_premises,
    build_provenance,
    make_quarantined,
    parse_iso_datetime,
    parse_json_records,
    require_non_empty,
    resolve_premises_type,
    validate_fssai_id,
)
from india_ate.adapters._hygiene_parser import optional_str
from india_ate.adapters.http import HttpFetcher, HttpxFetcher
from india_ate.models import BrandListing, IngestionBatch, QuarantinedRecord

DEFAULT_ONDC_URL = "https://ondc.org/catalog/fb/snapshot"


class ONDCCatalogAdapter(BaseSourceAdapter):
    """Adapter for ONDC F&B open catalog seller-to-FSSAI mappings."""

    source_name = "ONDC Open F&B Catalog"
    jurisdiction_iso = "IN"

    def __init__(
        self,
        fetcher: HttpFetcher | None = None,
        portal_url: str = DEFAULT_ONDC_URL,
    ) -> None:
        self._fetcher: HttpFetcher = fetcher or HttpxFetcher()
        self.portal_url = portal_url
        self._content_sha256 = hashlib.sha256(b"").hexdigest()
        self._retrieved_at = datetime.now(UTC)

    def fetch(self) -> bytes:
        """Fetch raw ONDC catalog snapshot bytes via injected HttpFetcher."""
        raw = self._fetcher.get(self.portal_url)
        self._content_sha256 = hashlib.sha256(raw).hexdigest()
        self._retrieved_at = datetime.now(UTC)
        return raw

    def parse(self, raw: bytes) -> list[dict[str, Any]]:
        """Parse raw JSON bytes into candidate ONDC catalog dictionaries."""
        self._content_sha256 = hashlib.sha256(raw).hexdigest()
        self._retrieved_at = datetime.now(UTC)
        return parse_json_records(raw)

    def _emit_one(self, record: dict[str, Any]) -> tuple[BaseModel, BrandListing]:
        fssai_id = validate_fssai_id(record)
        legal_name = require_non_empty(record, "legal_name", "legal_name")
        display_name = require_non_empty(record, "display_name", "display_name")
        ptype = resolve_premises_type(record, default="restaurant")
        seen_at = parse_iso_datetime(record, "seen_at", self._retrieved_at)
        prov = build_provenance(
            self.source_name, self.portal_url, self._retrieved_at, self._content_sha256
        )
        premises = build_fssai_premises(record, fssai_id, legal_name, ptype, prov)
        slug = hashlib.sha256(f"{fssai_id}:{display_name}".encode()).hexdigest()[:12]
        listing = BrandListing(
            listing_id=f"listing:ondc:{fssai_id}:{slug}",
            display_name=display_name,
            platform="ondc",
            premises_entity_id=premises.entity_id,
            postal_code=optional_str(record.get("postal_code")),
            first_seen_at=seen_at,
            last_seen_at=seen_at,
            provenance=prov,
        )
        return premises, listing

    def validate_and_emit_batch(self, records: list[dict[str, Any]]) -> IngestionBatch:
        """Validate ONDC catalog records strictly and quarantine invalid rows."""
        entities: list[BaseModel] = []
        quarantined: list[QuarantinedRecord] = []
        for record in records:
            try:
                premises, listing = self._emit_one(record)
            except ValueError as exc:
                quarantined.append(
                    make_quarantined(
                        self.source_name, record, str(exc), self._retrieved_at
                    )
                )
                continue
            entities.extend([premises, listing])
        return IngestionBatch(entities=entities, quarantined=quarantined)

    def validate_and_emit(self, records: list[dict[str, Any]]) -> list[BaseModel]:
        """Return only validated entities, routing invalid rows to quarantine."""
        return self.validate_and_emit_batch(records).entities
