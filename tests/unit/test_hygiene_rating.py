"""Unit tests for HygieneRatingAdapter."""

import hashlib
from pathlib import Path

from india_ate.adapters.hygiene_rating import HygieneRatingAdapter
from india_ate.models import AuthoritativeEvent, FoodPremises

FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures"


class _StubFetcher:
    def __init__(self, payload: bytes) -> None:
        self.payload = payload
        self.requested_urls: list[tuple[str, dict[str, str] | None]] = []

    def get(
        self,
        url: str,
        params: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
    ) -> bytes:
        self.requested_urls.append((url, params))
        return self.payload

    def post(
        self,
        url: str,
        data: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
    ) -> bytes:
        return self.payload


def test_hygiene_adapter_html_snapshot_emits_and_quarantines() -> None:
    raw = (FIXTURES_DIR / "hygiene_sample.html").read_bytes()
    fetcher = _StubFetcher(raw)
    adapter = HygieneRatingAdapter(
        fetcher=fetcher,
        portal_url="https://hygiene.fssai.gov.in/snapshot",
        state_code="15",
    )

    fetched = adapter.fetch()
    assert fetched == raw
    assert fetcher.requested_urls == [
        ("https://hygiene.fssai.gov.in/snapshot", {"state": "15"})
    ]

    records = adapter.parse(fetched)
    batch = adapter.validate_and_emit_batch(records)

    assert len(batch.entities) == 2
    assert len(batch.quarantined) == 1

    premises = batch.entities[0]
    event = batch.entities[1]
    assert isinstance(premises, FoodPremises)
    assert isinstance(event, AuthoritativeEvent)
    assert premises.entity_id == "actor:in:fssai:10013022000417"
    assert premises.legal_name == "Acme Foods Pvt Ltd"
    assert event.event_type == "hygiene_audit"
    assert event.status == "5/5"

    expected_sha = hashlib.sha256(raw).hexdigest()
    assert premises.provenance[0].content_sha256 == expected_sha
    assert event.provenance.content_sha256 == expected_sha
    assert "14-digit" in batch.quarantined[0].reason


def test_hygiene_adapter_json_snapshot_and_validate_and_emit() -> None:
    raw = (FIXTURES_DIR / "hygiene_sample.json").read_bytes()
    fetcher = _StubFetcher(raw)
    adapter = HygieneRatingAdapter(fetcher=fetcher)

    records = adapter.parse(adapter.fetch())
    entities = adapter.validate_and_emit(records)
    assert len(entities) == 2
    assert isinstance(entities[0], FoodPremises)
    assert entities[0].entity_id == "actor:in:fssai:22711126011608"


def test_hygiene_adapter_quarantines_devanagari_and_missing_fields() -> None:
    adapter = HygieneRatingAdapter(fetcher=_StubFetcher(b"[]"))
    rows = [
        {
            "fssai_id": "",
            "legal_name": "A",
            "rating": "4/5",
            "audit_date": "2026-02-14",
        },
        {
            "fssai_id": "१००१३०२२०००४१७",
            "legal_name": "B",
            "rating": "4/5",
            "audit_date": "2026-02-14",
        },
        {
            "fssai_id": "10411012000075",
            "legal_name": "",
            "rating": "4/5",
            "audit_date": "2026-02-14",
        },
        {
            "fssai_id": "10411012000075",
            "legal_name": "C",
            "rating": "",
            "audit_date": "2026-02-14",
        },
        {
            "fssai_id": "10411012000075",
            "legal_name": "D",
            "rating": "3/5",
            "audit_date": "not-a-date",
        },
        {
            "fssai_id": "10411012000075",
            "legal_name": "E",
            "premises_type": "spaceship",
            "rating": "3/5",
            "audit_date": "2026-02-14",
        },
        {
            "fssai_id": "99999999999999",
            "legal_name": "F",
            "rating": "3/5",
            "audit_date": "2026-02-14",
        },
    ]
    batch = adapter.validate_and_emit_batch(rows)
    assert batch.entities == []
    assert len(batch.quarantined) == 7
    assert "fssai" in batch.quarantined[0].reason.lower()
    assert "ASCII" in batch.quarantined[1].reason
    assert "legal_name" in batch.quarantined[2].reason
    assert "rating" in batch.quarantined[3].reason
    assert "audit_date" in batch.quarantined[4].reason
    assert "premises_type" in batch.quarantined[5].reason
    assert "tier" in batch.quarantined[6].reason.lower()


def test_hygiene_adapter_parse_edge_cases() -> None:
    adapter = HygieneRatingAdapter(fetcher=_StubFetcher(b"[]"))
    assert len(adapter.parse(b'[{"fssai_id": "123"}]')) == 1
    assert len(adapter.parse(b'{"fssai_id": "123"}')) == 1
    assert adapter.parse(b'"scalar"') == []
    assert adapter.parse(b"<html><body><p>No table</p></body></html>") == []
    assert adapter.parse(b"<table><tr><td>No headers</td></tr></table>") == []
