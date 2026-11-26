"""Unit tests for HygieneRatingAdapter."""

import hashlib
import json
from datetime import UTC
from pathlib import Path

import pytest

from india_ate.adapters._hygiene_parser import clean_str, optional_str
from india_ate.adapters.hygiene_rating import (
    DEFAULT_HYGIENE_URL,
    HygieneRatingAdapter,
)
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
    assert adapter.parse(b"") == []
    assert len(adapter.parse(b'[{"fssai_id": "123"}]')) == 1
    assert len(adapter.parse(b'   \n[{"fssai_id": "123"}]')) == 1
    assert len(adapter.parse(b'{"fssai_id": "123"}')) == 1
    assert adapter.parse(b'"scalar"') == []
    assert adapter.parse(b"<html><body><p>No table</p></body></html>") == []
    assert adapter.parse(b"<table><tr><td>No headers</td></tr></table>") == []

    # Non-dict JSON items are filtered out
    mixed = b'{"records": [123, "bad", {"fssai_id": "10013022000417"}]}'
    assert adapter.parse(mixed) == [{"fssai_id": "10013022000417"}]

    # Invalid JSON raises JSONDecodeError
    with pytest.raises(json.JSONDecodeError):
        adapter.parse(b"{invalid json")

    # Malformed HTML with preceding div, padded headers/cells, and mismatched row
    html = (
        b"<div><p>Banner</p></div>"
        b"<table><tr><th> FSSAI_ID </th><th> Legal_Name </th></tr>"
        b"<tr><td>  10013022000417  </td><td>  Acme Foods  </td></tr>"
        b"<tr><td>only-one-cell</td></tr>"
        b"</table>"
    )
    assert adapter.parse(html) == [
        {"fssai_id": "10013022000417", "legal_name": "Acme Foods"}
    ]


def test_hygiene_adapter_optional_fields_default_type_and_provenance() -> None:
    assert clean_str(123) == ""
    assert clean_str("  hi  ") == "hi"
    assert optional_str("   ") is None
    assert optional_str("  Mumbai  ") == "Mumbai"

    raw = b'[{"fssai_id": "10013022000417", "legal_name": "Acme"}]'
    fetcher = _StubFetcher(raw)
    adapter = HygieneRatingAdapter(fetcher=fetcher)

    # Default provenance before fetch/parse
    batch_initial = adapter.validate_and_emit_batch(
        [
            {
                "fssai_id": "10013022000417",
                "legal_name": "Acme",
                "rating": "5/5",
                "audit_date": "2026-02-14",
                "address": "  12 MG Road  ",
                "postal_code": " 400001 ",
                "city": " Mumbai ",
                "state": " Maharashtra ",
            }
        ]
    )
    premises = batch_initial.entities[0]
    assert isinstance(premises, FoodPremises)
    assert premises.premises_type == "restaurant"
    assert premises.address == "12 MG Road"
    assert premises.postal_code == "400001"
    assert premises.city == "Mumbai"
    assert premises.state == "Maharashtra"
    assert premises.provenance[0].content_sha256 == hashlib.sha256(b"").hexdigest()
    assert premises.provenance[0].retrieved_at.tzinfo == UTC

    # fetch() with state_code=None passes params=None and updates sha256
    fetched = adapter.fetch()
    assert fetched == raw
    assert fetcher.requested_urls == [(DEFAULT_HYGIENE_URL, None)]
    batch_after_fetch = adapter.validate_and_emit_batch(
        [
            {
                "fssai_id": "10013022000417",
                "legal_name": "Acme",
                "rating": "5/5",
                "audit_date": "2026-02-14",
            }
        ]
    )
    p2 = batch_after_fetch.entities[0]
    assert isinstance(p2, FoodPremises)
    assert p2.provenance[0].content_sha256 == hashlib.sha256(raw).hexdigest()
    assert p2.provenance[0].retrieved_at.tzinfo == UTC


def test_hygiene_adapter_exact_validation_error_messages() -> None:
    adapter = HygieneRatingAdapter(fetcher=_StubFetcher(b"[]"))
    rows = [
        {
            "fssai_id": "",
            "legal_name": "A",
            "rating": "5/5",
            "audit_date": "2026-02-14",
        },
        {
            "fssai_id": "१००१३०२२०००४१७",
            "legal_name": "B",
            "rating": "5/5",
            "audit_date": "2026-02-14",
        },
        {
            "fssai_id": "1001302200041a",
            "legal_name": "C",
            "rating": "5/5",
            "audit_date": "2026-02-14",
        },
        {
            "fssai_id": "10013022000417",
            "legal_name": "D",
            "rating": "5/5",
            "audit_date": "bad-date",
        },
    ]
    batch = adapter.validate_and_emit_batch(rows)
    assert [q.reason for q in batch.quarantined] == [
        "Missing mandatory fssai_id",
        "FSSAI ID must contain ASCII digits only",
        "FSSAI ID must be a 14-digit numeric string",
        "Missing or invalid audit_date",
    ]
