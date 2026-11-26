"""Unit tests for BaseSourceAdapter abstract contract and quarantine behavior."""

import inspect
import json
from datetime import UTC, date, datetime
from typing import Any

import pytest
from pydantic import BaseModel, HttpUrl, ValidationError

from india_ate.adapters import BaseSourceAdapter
from india_ate.models import AuthoritativeEvent, EvidenceProvenance


class _OfflineRecallAdapter(BaseSourceAdapter):
    """Test concrete adapter demonstrating deterministic quarantine."""

    source_name = "FoSCoS Recall Portal"
    jurisdiction_iso = "IN"

    def __init__(self, fixture_bytes: bytes) -> None:
        self._fixture_bytes = fixture_bytes
        self.quarantined: list[dict[str, Any]] = []

    def fetch(self) -> bytes:
        return self._fixture_bytes

    def parse(self, raw: bytes) -> list[dict[str, Any]]:
        data: list[dict[str, Any]] = json.loads(raw.decode("utf-8"))
        return data

    def validate_and_emit(self, records: list[dict[str, Any]]) -> list[BaseModel]:
        emitted: list[BaseModel] = []
        for rec in records:
            try:
                prov = rec["provenance"]
                event = AuthoritativeEvent(
                    event_id=rec["event_id"],
                    event_type=rec["event_type"],
                    target_entity_id=rec["target_entity_id"],
                    jurisdiction_iso=self.jurisdiction_iso,
                    event_date=date.fromisoformat(rec["event_date"]),
                    status=rec["status"],
                    batch_or_lot_no=rec.get("batch_or_lot_no"),
                    verbatim_summary=rec["verbatim_summary"],
                    provenance=EvidenceProvenance(
                        source_name=self.source_name,
                        source_url=HttpUrl(prov["source_url"]),
                        retrieved_at=datetime.fromisoformat(prov["retrieved_at"]),
                        content_sha256=prov["content_sha256"],
                        verification_tier=prov["verification_tier"],
                    ),
                )
                emitted.append(event)
            except (KeyError, TypeError, ValueError, ValidationError):
                self.quarantined.append(rec)
        return emitted


def test_base_source_adapter_is_abstract() -> None:
    assert inspect.isabstract(BaseSourceAdapter)
    assert BaseSourceAdapter.__abstractmethods__ == {
        "fetch",
        "parse",
        "validate_and_emit",
    }
    with pytest.raises(TypeError):
        BaseSourceAdapter()  # type: ignore[abstract]


def test_concrete_adapter_emits_valid_and_quarantines_ambiguous() -> None:
    payload = [
        {
            "event_id": "evt:foscos:recall:2026-001",
            "event_type": "food_recall",
            "target_entity_id": "item:gtin:8901234567890",
            "event_date": "2026-03-20",
            "status": "Initiated",
            "batch_or_lot_no": "LOT-MH-2026-09",
            "verbatim_summary": "Voluntary recall initiated.",
            "provenance": {
                "source_url": "https://foscos.fssai.gov.in/recalls",
                "retrieved_at": datetime(2026, 4, 1, 10, 0, tzinfo=UTC).isoformat(),
                "content_sha256": (
                    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
                ),
                "verification_tier": "official_registry",
            },
        },
        {
            "event_id": "evt:foscos:recall:ambiguous",
            "event_type": "food_recall",
            "event_date": "2026-03-20",
            "status": "Initiated",
            "verbatim_summary": "Missing target_entity_id and content_sha256.",
            "provenance": {
                "source_url": "https://foscos.fssai.gov.in/recalls",
                "retrieved_at": "2026-04-01T10:00:00Z",
                "verification_tier": "official_registry",
            },
        },
    ]
    adapter = _OfflineRecallAdapter(json.dumps(payload).encode("utf-8"))
    raw = adapter.fetch()
    parsed = adapter.parse(raw)
    emitted = adapter.validate_and_emit(parsed)

    assert len(emitted) == 1
    assert isinstance(emitted[0], AuthoritativeEvent)
    assert len(adapter.quarantined) == 1
    assert adapter.quarantined[0]["event_id"] == "evt:foscos:recall:ambiguous"
