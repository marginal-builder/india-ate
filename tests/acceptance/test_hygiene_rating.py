"""Acceptance tests for features/adapters/hygiene_rating.feature."""

import hashlib
import json
import shlex
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

import pytest
from click.testing import CliRunner
from pydantic import HttpUrl, ValidationError
from pytest_bdd import given, parsers, scenarios, then, when

from india_ate.adapters.hygiene_rating import HygieneRatingAdapter
from india_ate.cli import app
from india_ate.models import (
    AuthoritativeEvent,
    BrandListing,
    EvidenceProvenance,
    FoodPremises,
    IndiaFSSAI14,
    IngestionBatch,
    QuarantinedRecord,
)
from india_ate.store import SQLiteStore

FEATURE_PATH = (
    Path(__file__).resolve().parents[2]
    / "features"
    / "adapters"
    / "hygiene_rating.feature"
)
scenarios(str(FEATURE_PATH))


class _StubFetcher:
    def __init__(self, payload: bytes) -> None:
        self.payload = payload
        self.requested_urls: list[str] = []

    def get(
        self,
        url: str,
        params: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
    ) -> bytes:
        self.requested_urls.append(url)
        return self.payload

    def post(
        self,
        url: str,
        data: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
    ) -> bytes:
        return self.payload


@pytest.fixture
def ctx(tmp_path: Path) -> dict[str, Any]:
    return {"tmp_path": tmp_path, "runner": CliRunner()}


@given(
    parsers.parse(
        'a QuarantinedRecord with source_name "{source}", raw_record containing '
        'fssai_id "{fssai_id}", reason "{reason}", and quarantined_at "{ts}"'
    )
)
def given_quarantined_record(
    ctx: dict[str, Any], source: str, fssai_id: str, reason: str, ts: str
) -> None:
    ctx["quarantined"] = QuarantinedRecord(
        source_name=source,
        raw_record={"fssai_id": fssai_id},
        reason=reason,
        quarantined_at=datetime.fromisoformat(ts.replace("Z", "+00:00")),
    )


@then("the QuarantinedRecord is valid")
def then_quarantined_valid(ctx: dict[str, Any]) -> None:
    assert isinstance(ctx["quarantined"], QuarantinedRecord)


@when("I attempt to mutate the reason field on the QuarantinedRecord")
def when_mutate_quarantined_reason(ctx: dict[str, Any]) -> None:
    try:
        ctx["quarantined"].reason = "changed"
    except ValidationError as exc:
        ctx["validation_error"] = exc


@when(
    parsers.parse(
        "I attempt to create a QuarantinedRecord with integer {val:d} as source_name"
    )
)
def when_create_quarantined_int_source(ctx: dict[str, Any], val: int) -> None:
    try:
        QuarantinedRecord(
            source_name=val,  # type: ignore[arg-type]
            raw_record={},
            reason="bad",
            quarantined_at=datetime(2026, 4, 1, tzinfo=UTC),
        )
    except ValidationError as exc:
        ctx["validation_error"] = exc


@given("an empty IngestionBatch with default fields")
def given_empty_batch(ctx: dict[str, Any]) -> None:
    ctx["batch"] = IngestionBatch()


@then("its entities list is empty")
def then_batch_entities_empty(ctx: dict[str, Any]) -> None:
    assert ctx["batch"].entities == []


@then("its quarantined list is empty")
def then_batch_quarantined_empty(ctx: dict[str, Any]) -> None:
    assert ctx["batch"].quarantined == []


@when("I attempt to mutate the entities field on the IngestionBatch")
def when_mutate_batch_entities(ctx: dict[str, Any]) -> None:
    try:
        ctx["batch"].entities = []
    except ValidationError as exc:
        ctx["validation_error"] = exc


@then("a ValidationError is raised")
def then_validation_error_raised(ctx: dict[str, Any]) -> None:
    assert isinstance(ctx.get("validation_error"), ValidationError)


@given(
    parsers.parse(
        'a deterministic offline HttpFetcher returning an HTML snapshot for "{source}" '
        'from URL "{url}"'
    )
)
def given_html_fetcher(ctx: dict[str, Any], source: str, url: str) -> None:
    ctx["portal_url"] = url
    ctx["source_name"] = source


@given(
    parsers.parse(
        'the HTML snapshot contains a valid eatery row with fssai_id "{fssai_id}", '
        'legal_name "{legal_name}", premises_type "{ptype}", address "{address}", '
        'postal_code "{postal_code}", city "{city}", state "{state}", '
        'rating "{rating}", and audit_date "{audit_date}"'
    )
)
def given_html_row(
    ctx: dict[str, Any],
    fssai_id: str,
    legal_name: str,
    ptype: str,
    address: str,
    postal_code: str,
    city: str,
    state: str,
    rating: str,
    audit_date: str,
) -> None:
    html = (
        "<table><thead><tr>"
        "<th>fssai_id</th><th>legal_name</th><th>premises_type</th>"
        "<th>address</th><th>postal_code</th><th>city</th><th>state</th>"
        "<th>rating</th><th>audit_date</th>"
        "</tr></thead><tbody><tr>"
        f"<td>{fssai_id}</td><td>{legal_name}</td><td>{ptype}</td>"
        f"<td>{address}</td><td>{postal_code}</td><td>{city}</td>"
        f"<td>{state}</td><td>{rating}</td><td>{audit_date}</td>"
        "</tr></tbody></table>"
    ).encode()
    ctx["raw_bytes"] = html
    ctx["fetcher"] = _StubFetcher(html)
    ctx["adapter"] = HygieneRatingAdapter(
        fetcher=ctx["fetcher"], portal_url=ctx["portal_url"]
    )


@given(
    parsers.parse(
        'a deterministic offline HttpFetcher returning a JSON snapshot for "{source}" '
        'from URL "{url}"'
    )
)
def given_json_fetcher(ctx: dict[str, Any], source: str, url: str) -> None:
    ctx["portal_url"] = url
    ctx["source_name"] = source


@given(
    parsers.parse(
        'the JSON snapshot contains a valid eatery row with fssai_id "{fssai_id}", '
        'legal_name "{legal_name}", premises_type "{ptype}", address "{address}", '
        'postal_code "{postal_code}", city "{city}", state "{state}", '
        'rating "{rating}", and audit_date "{audit_date}"'
    )
)
def given_json_row(
    ctx: dict[str, Any],
    fssai_id: str,
    legal_name: str,
    ptype: str,
    address: str,
    postal_code: str,
    city: str,
    state: str,
    rating: str,
    audit_date: str,
) -> None:
    payload = json.dumps(
        {
            "records": [
                {
                    "fssai_id": fssai_id,
                    "legal_name": legal_name,
                    "premises_type": ptype,
                    "address": address,
                    "postal_code": postal_code,
                    "city": city,
                    "state": state,
                    "rating": rating,
                    "audit_date": audit_date,
                }
            ]
        }
    ).encode("utf-8")
    ctx["raw_bytes"] = payload
    ctx["fetcher"] = _StubFetcher(payload)
    ctx["adapter"] = HygieneRatingAdapter(
        fetcher=ctx["fetcher"], portal_url=ctx["portal_url"]
    )


@given(
    parsers.re(
        r"a deterministic offline HttpFetcher returning a JSON snapshot with 1 "
        r'invalid row having fssai_id "(?P<fssai_id>[^"]*)", legal_name '
        r'"(?P<legal_name>[^"]*)", rating "(?P<rating>[^"]*)", and audit_date '
        r'"(?P<audit_date>[^"]*)"'
    )
)
def given_invalid_json_row(
    ctx: dict[str, Any],
    fssai_id: str,
    legal_name: str,
    rating: str,
    audit_date: str,
) -> None:
    payload = json.dumps(
        {
            "records": [
                {
                    "fssai_id": fssai_id,
                    "legal_name": legal_name,
                    "rating": rating,
                    "audit_date": audit_date,
                }
            ]
        }
    ).encode("utf-8")
    ctx["raw_bytes"] = payload
    ctx["fetcher"] = _StubFetcher(payload)
    ctx["adapter"] = HygieneRatingAdapter(fetcher=ctx["fetcher"])


@given(
    parsers.parse(
        "a deterministic offline HttpFetcher returning a JSON snapshot with 1 valid "
        'row for fssai_id "{valid_id}" and 1 invalid row with fssai_id "{bad_id}"'
    )
)
def given_mixed_json_snapshot(ctx: dict[str, Any], valid_id: str, bad_id: str) -> None:
    payload = json.dumps(
        {
            "records": [
                {
                    "fssai_id": valid_id,
                    "legal_name": "Valid Eatery",
                    "premises_type": "restaurant",
                    "rating": "4/5",
                    "audit_date": "2026-02-14",
                },
                {
                    "fssai_id": bad_id,
                    "legal_name": "Invalid Eatery",
                    "rating": "4/5",
                    "audit_date": "2026-02-14",
                },
            ]
        }
    ).encode("utf-8")
    ctx["raw_bytes"] = payload
    ctx["fetcher"] = _StubFetcher(payload)
    ctx["adapter"] = HygieneRatingAdapter(fetcher=ctx["fetcher"])


@when(
    "I run HygieneRatingAdapter fetch(), parse(raw), and "
    "validate_and_emit_batch(records)"
)
def when_run_adapter_pipeline(ctx: dict[str, Any]) -> None:
    adapter: HygieneRatingAdapter = ctx["adapter"]
    raw = adapter.fetch()
    records = adapter.parse(raw)
    ctx["batch"] = adapter.validate_and_emit_batch(records)


@then("the IngestionBatch contains 1 FoodPremises and 1 AuthoritativeEvent")
def then_batch_has_1_premises_1_event(ctx: dict[str, Any]) -> None:
    batch: IngestionBatch = ctx["batch"]
    assert sum(1 for e in batch.entities if isinstance(e, FoodPremises)) == 1
    assert sum(1 for e in batch.entities if isinstance(e, AuthoritativeEvent)) == 1


@then("the IngestionBatch quarantined list is empty")
def then_batch_quarantine_is_empty(ctx: dict[str, Any]) -> None:
    assert ctx["batch"].quarantined == []


@then("the IngestionBatch entities list is empty")
def then_batch_entities_is_empty(ctx: dict[str, Any]) -> None:
    assert ctx["batch"].entities == []


@then(parsers.parse("the IngestionBatch quarantined list has length {n:d}"))
def then_batch_quarantine_len(ctx: dict[str, Any], n: int) -> None:
    assert len(ctx["batch"].quarantined) == n


@then(
    parsers.parse(
        'the emitted FoodPremises has entity_id "{entity_id}" and legal_name "{name}"'
    )
)
def then_premises_id_and_name(ctx: dict[str, Any], entity_id: str, name: str) -> None:
    premises = next(e for e in ctx["batch"].entities if isinstance(e, FoodPremises))
    assert premises.entity_id == entity_id
    assert premises.legal_name == name


@then(
    parsers.parse(
        'the emitted FoodPremises has entity_id "{entity_id}" and state "{state}"'
    )
)
def then_premises_id_and_state(ctx: dict[str, Any], entity_id: str, state: str) -> None:
    premises = next(e for e in ctx["batch"].entities if isinstance(e, FoodPremises))
    assert premises.entity_id == entity_id
    assert premises.state == state


@then(
    parsers.parse(
        'the emitted FoodPremises has regulatory_ids containing IndiaFSSAI14 "{fid}"'
    )
)
def then_premises_has_fssai(ctx: dict[str, Any], fid: str) -> None:
    premises = next(e for e in ctx["batch"].entities if isinstance(e, FoodPremises))
    assert any(
        isinstance(reg, IndiaFSSAI14) and reg.raw_value == fid
        for reg in premises.regulatory_ids
    )


@then(
    parsers.parse(
        'the emitted AuthoritativeEvent has event_type "{etype}", target_entity_id '
        '"{target}", status "{status}", and event_date "{edate}"'
    )
)
def then_event_fields_with_date(
    ctx: dict[str, Any], etype: str, target: str, status: str, edate: str
) -> None:
    event = next(e for e in ctx["batch"].entities if isinstance(e, AuthoritativeEvent))
    assert event.event_type == etype
    assert event.target_entity_id == target
    assert event.status == status
    assert event.event_date.isoformat() == edate


@then(
    parsers.parse(
        'the emitted AuthoritativeEvent has event_type "{etype}", target_entity_id '
        '"{target}", and status "{status}"'
    )
)
def then_event_fields(
    ctx: dict[str, Any], etype: str, target: str, status: str
) -> None:
    event = next(e for e in ctx["batch"].entities if isinstance(e, AuthoritativeEvent))
    assert event.event_type == etype
    assert event.target_entity_id == target
    assert event.status == status


@then(
    parsers.parse(
        "both emitted entities carry EvidenceProvenance with verification_tier "
        '"{tier}" and content_sha256 matching the SHA-256 of the raw snapshot bytes'
    )
)
def then_entities_provenance(ctx: dict[str, Any], tier: str) -> None:
    expected_sha = hashlib.sha256(ctx["raw_bytes"]).hexdigest()
    premises = next(e for e in ctx["batch"].entities if isinstance(e, FoodPremises))
    event = next(e for e in ctx["batch"].entities if isinstance(e, AuthoritativeEvent))
    assert premises.provenance[0].verification_tier == tier
    assert premises.provenance[0].content_sha256 == expected_sha
    assert event.provenance.verification_tier == tier
    assert event.provenance.content_sha256 == expected_sha


@then(parsers.parse('the quarantined record has source_name "{source}"'))
def then_quarantined_source(ctx: dict[str, Any], source: str) -> None:
    assert ctx["batch"].quarantined[0].source_name == source


@then(parsers.parse('the quarantined record reason contains "{expected}"'))
def then_quarantined_reason_contains(ctx: dict[str, Any], expected: str) -> None:
    assert expected.lower() in ctx["batch"].quarantined[0].reason.lower()


@then("the quarantined record preserves the original raw_record")
def then_quarantined_preserves_raw(ctx: dict[str, Any]) -> None:
    assert isinstance(ctx["batch"].quarantined[0].raw_record, dict)
    assert "fssai_id" in ctx["batch"].quarantined[0].raw_record


@then(
    parsers.parse(
        "the IngestionBatch contains 1 FoodPremises and 1 AuthoritativeEvent for "
        '"{entity_id}"'
    )
)
def then_mixed_batch_entities(ctx: dict[str, Any], entity_id: str) -> None:
    premises = next(e for e in ctx["batch"].entities if isinstance(e, FoodPremises))
    event = next(e for e in ctx["batch"].entities if isinstance(e, AuthoritativeEvent))
    assert premises.entity_id == entity_id
    assert event.target_entity_id == entity_id


@then(
    parsers.parse(
        'the IngestionBatch quarantined list has length {n:d} for raw fssai_id "{fid}"'
    )
)
def then_mixed_batch_quarantine(ctx: dict[str, Any], n: int, fid: str) -> None:
    assert len(ctx["batch"].quarantined) == n
    assert ctx["batch"].quarantined[0].raw_record["fssai_id"] == fid


@given(
    "a custom HttpFetcher stub that records requested URLs and returns deterministic "
    "bytes without network access"
)
def given_custom_stub_fetcher(ctx: dict[str, Any]) -> None:
    ctx["stub_bytes"] = b"<html>stub</html>"
    ctx["fetcher"] = _StubFetcher(ctx["stub_bytes"])
    ctx["portal_url"] = "https://hygiene.fssai.gov.in/custom"
    ctx["adapter"] = HygieneRatingAdapter(
        fetcher=ctx["fetcher"], portal_url=ctx["portal_url"]
    )


@when("HygieneRatingAdapter.fetch() is invoked")
def when_adapter_fetch_invoked(ctx: dict[str, Any]) -> None:
    ctx["fetched_bytes"] = ctx["adapter"].fetch()


@then("the custom HttpFetcher receives the configured portal URL")
def then_fetcher_received_url(ctx: dict[str, Any]) -> None:
    assert ctx["fetcher"].requested_urls == [ctx["portal_url"]]


@then("zero external network connections are attempted")
def then_zero_network_calls(ctx: dict[str, Any]) -> None:
    assert len(ctx["fetcher"].requested_urls) == 1


@then("the returned bytes match the stub response verbatim")
def then_bytes_match_stub(ctx: dict[str, Any]) -> None:
    assert ctx["fetched_bytes"] == ctx["stub_bytes"]


@given("an initialized SQLiteStore")
def given_initialized_store(ctx: dict[str, Any]) -> None:
    store = SQLiteStore(":memory:")
    store.initialize()
    ctx["store"] = store


@given(
    parsers.parse(
        'an IngestionBatch containing FoodPremises "{entity_id}", AuthoritativeEvent '
        '"{event_id}", and 1 QuarantinedRecord for raw fssai_id "{bad_id}"'
    )
)
def given_store_batch(
    ctx: dict[str, Any], entity_id: str, event_id: str, bad_id: str
) -> None:
    fssai_id = entity_id.split(":")[-1]
    prov = EvidenceProvenance(
        source_name="FSSAI Hygiene Rating Portal",
        source_url=HttpUrl("https://hygiene.fssai.gov.in/snapshot"),
        retrieved_at=datetime(2026, 4, 1, tzinfo=UTC),
        content_sha256="abc123",
        verification_tier="official_registry",
    )
    premises = FoodPremises(
        entity_id=entity_id,
        legal_name="Eastern Foods",
        jurisdiction_iso="IN",
        regulatory_ids=[IndiaFSSAI14(raw_value=fssai_id)],
        provenance=[prov],
        premises_type="restaurant",
    )
    event = AuthoritativeEvent(
        event_id=event_id,
        event_type="hygiene_audit",
        target_entity_id=entity_id,
        jurisdiction_iso="IN",
        event_date=date(2026, 3, 1),
        status="5/5",
        verbatim_summary="FSSAI Hygiene Rating 5/5",
        provenance=prov,
    )
    quarantined = QuarantinedRecord(
        source_name="FSSAI Hygiene Rating Portal",
        raw_record={"fssai_id": bad_id},
        reason="Invalid 14-digit FSSAI ID",
        quarantined_at=datetime(2026, 4, 1, tzinfo=UTC),
    )
    ctx["batch"] = IngestionBatch(entities=[premises, event], quarantined=[quarantined])


@when("I call save_ingestion_batch on the SQLiteStore")
def when_save_ingestion_batch(ctx: dict[str, Any]) -> None:
    ctx["store"].save_ingestion_batch(ctx["batch"])


@then(parsers.parse('getting FoodPremises by FSSAI ID "{fid}" returns "{entity_id}"'))
def then_get_premises_by_fssai(ctx: dict[str, Any], fid: str, entity_id: str) -> None:
    loaded = ctx["store"].get_premises_by_fssai_id(fid)
    assert loaded is not None
    assert loaded.entity_id == entity_id


@then(
    parsers.parse(
        'retrieving AuthoritativeEvents for "{entity_id}" returns 1 event with '
        'event_type "{etype}"'
    )
)
def then_get_events_for_target(ctx: dict[str, Any], entity_id: str, etype: str) -> None:
    events = ctx["store"].get_events_for_target(entity_id)
    assert len(events) == 1
    assert events[0].event_type == etype


@then(
    "list_quarantined on the SQLiteStore returns 1 QuarantinedRecord with reason "
    "preserved"
)
def then_list_quarantined_returns_1(ctx: dict[str, Any]) -> None:
    records = ctx["store"].list_quarantined()
    assert len(records) == 1
    assert records[0].reason == "Invalid 14-digit FSSAI ID"


@given(
    parsers.parse(
        'a local HTML hygiene rating snapshot file containing valid eatery "{fid}" '
        "and 1 malformed row"
    )
)
def given_local_html_snapshot(ctx: dict[str, Any], fid: str) -> None:
    snapshot_path = ctx["tmp_path"] / "snapshot.html"
    html = (
        "<table><thead><tr>"
        "<th>fssai_id</th><th>legal_name</th><th>premises_type</th>"
        "<th>rating</th><th>audit_date</th>"
        "</tr></thead><tbody>"
        f"<tr><td>{fid}</td><td>Acme Foods</td><td>restaurant</td>"
        "<td>5/5</td><td>2026-02-14</td></tr>"
        "<tr><td>bad</td><td>Bad Row</td><td>restaurant</td>"
        "<td>4/5</td><td>2026-02-14</td></tr>"
        "</tbody></table>"
    )
    snapshot_path.write_text(html, encoding="utf-8")
    ctx["snapshot_path"] = snapshot_path


@given(
    parsers.parse(
        'a SQLiteStore at a temporary database path with a BrandListing "{lid}" '
        'linked to "{entity_id}"'
    )
)
def given_temp_db_with_listing(ctx: dict[str, Any], lid: str, entity_id: str) -> None:
    db_path = ctx["tmp_path"] / "test.db"
    prov = EvidenceProvenance(
        source_name="Swiggy Storefront Snapshot",
        source_url=HttpUrl("https://www.swiggy.com/restaurants/77"),
        retrieved_at=datetime(2026, 4, 1, tzinfo=UTC),
        content_sha256="listinghash",
        verification_tier="user_verified_snapshot",
    )
    listing = BrandListing(
        listing_id=lid,
        display_name="Acme Ghost Kitchen",
        platform="swiggy",
        premises_entity_id=entity_id,
        first_seen_at=datetime(2026, 4, 1, tzinfo=UTC),
        last_seen_at=datetime(2026, 4, 1, tzinfo=UTC),
        provenance=prov,
    )
    with SQLiteStore(db_path) as store:
        store.initialize()
        store.save_brand_listing(listing)
    ctx["db_path"] = db_path


@when(parsers.parse('I run the CLI command "{cmd}"'))
def when_run_cli(ctx: dict[str, Any], cmd: str) -> None:
    resolved = cmd.replace("<snapshot>", str(ctx.get("snapshot_path", ""))).replace(
        "<path>", str(ctx.get("db_path", ""))
    )
    args = shlex.split(resolved)
    if args and args[0] == "india-ate":
        args = args[1:]
    ctx["cli_result"] = ctx["runner"].invoke(app, args)


@then(parsers.parse("the CLI exits with status code {code:d}"))
def then_cli_exit_code(ctx: dict[str, Any], code: int) -> None:
    assert ctx["cli_result"].exit_code == code, ctx["cli_result"].output


@then(
    "the CLI output reports 1 premises ingested, 1 event ingested, and 1 record "
    "quarantined"
)
def then_cli_ingest_summary(ctx: dict[str, Any]) -> None:
    summary = json.loads(ctx["cli_result"].output)
    assert summary["premises_ingested"] == 1
    assert summary["events_ingested"] == 1
    assert summary["quarantined"] == 1


@then(
    parsers.parse(
        "the stdout is valid Fact Receipt JSON containing decoded IndiaFSSAI14 fields "
        'for "{fid}"'
    )
)
def then_stdout_fact_receipt(ctx: dict[str, Any], fid: str) -> None:
    receipt = json.loads(ctx["cli_result"].output)
    ctx["receipt"] = receipt
    assert receipt["decoded"]["serial"] == fid[-6:]


@then(
    parsers.parse(
        'the Fact Receipt JSON includes the stored FoodPremises "{entity_id}"'
    )
)
def then_receipt_includes_premises(ctx: dict[str, Any], entity_id: str) -> None:
    assert ctx["receipt"]["premises"]["entity_id"] == entity_id


@then(parsers.parse('the Fact Receipt JSON includes the BrandListing "{lid}"'))
def then_receipt_includes_listing(ctx: dict[str, Any], lid: str) -> None:
    assert any(item["listing_id"] == lid for item in ctx["receipt"]["brand_listings"])


@then(
    parsers.parse(
        "the Fact Receipt JSON includes the hygiene_audit AuthoritativeEvent for "
        '"{entity_id}"'
    )
)
def then_receipt_includes_event(ctx: dict[str, Any], entity_id: str) -> None:
    assert any(
        evt["event_type"] == "hygiene_audit" and evt["target_entity_id"] == entity_id
        for evt in ctx["receipt"]["events"]
    )
