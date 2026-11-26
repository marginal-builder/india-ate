"""Acceptance tests for authoritative_event.feature."""

import inspect
import json
from datetime import date, datetime
from pathlib import Path
from typing import Any

import pytest
from pydantic import BaseModel, HttpUrl, ValidationError
from pytest_bdd import given, parsers, scenarios, then, when

from india_ate.adapters import BaseSourceAdapter
from india_ate.models import AuthoritativeEvent, EvidenceProvenance

FEATURE_PATH = (
    Path(__file__).resolve().parents[2]
    / "features"
    / "entity_graph"
    / "authoritative_event.feature"
)
scenarios(str(FEATURE_PATH))


class _FixtureRecallAdapter(BaseSourceAdapter):
    def __init__(self, source_name: str, jurisdiction_iso: str, raw: bytes) -> None:
        self.source_name = source_name
        self.jurisdiction_iso = jurisdiction_iso
        self._raw = raw
        self.quarantined: list[dict[str, Any]] = []

    def fetch(self) -> bytes:
        return self._raw

    def parse(self, raw: bytes) -> list[dict[str, Any]]:
        records: list[dict[str, Any]] = json.loads(raw.decode("utf-8"))
        return records

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


@pytest.fixture
def ctx(
    official_provenance: EvidenceProvenance,
    user_provenance: EvidenceProvenance,
) -> dict[str, Any]:
    return {
        "official_provenance": official_provenance,
        "user_provenance": user_provenance,
        "error": None,
        "emitted": [],
    }


@given(
    parsers.re(
        r'an AuthoritativeEvent with event_id "(?P<event_id>[^"]+)", event_type '
        r'"(?P<event_type>[^"]+)", target_entity_id "(?P<target_id>[^"]+)", '
        r'jurisdiction_iso "(?P<iso>[^"]+)", event_date "(?P<event_date>[^"]+)", '
        r'status "(?P<status>[^"]+)", batch_or_lot_no "(?P<lot_no>[^"]+)", '
        r'verbatim_summary "(?P<summary>[^"]+)", and valid official_registry '
        r"provenance"
    )
)
def given_recall_event(
    ctx: dict[str, Any],
    event_id: str,
    event_type: str,
    target_id: str,
    iso: str,
    event_date: str,
    status: str,
    lot_no: str,
    summary: str,
) -> None:
    ctx["event"] = AuthoritativeEvent(
        event_id=event_id,
        event_type=event_type,  # type: ignore[arg-type]
        target_entity_id=target_id,
        jurisdiction_iso=iso,
        event_date=date.fromisoformat(event_date),
        status=status,
        batch_or_lot_no=lot_no,
        verbatim_summary=summary,
        provenance=ctx["official_provenance"],
    )


@given(
    parsers.re(
        r'an AuthoritativeEvent with event_id "(?P<event_id>[^"]+)", event_type '
        r'"(?P<event_type>[^"]+)", target_entity_id "(?P<target_id>[^"]+)", '
        r'jurisdiction_iso "(?P<iso>[^"]+)", event_date "(?P<event_date>[^"]+)", '
        r'status "(?P<status>[^"]+)", verbatim_summary "(?P<summary>[^"]+)", '
        r"and valid official_registry provenance"
    )
)
def given_official_event(
    ctx: dict[str, Any],
    event_id: str,
    event_type: str,
    target_id: str,
    iso: str,
    event_date: str,
    status: str,
    summary: str,
) -> None:
    ctx["event"] = AuthoritativeEvent(
        event_id=event_id,
        event_type=event_type,  # type: ignore[arg-type]
        target_entity_id=target_id,
        jurisdiction_iso=iso,
        event_date=date.fromisoformat(event_date),
        status=status,
        verbatim_summary=summary,
        provenance=ctx["official_provenance"],
    )


@given(
    parsers.parse(
        'an AuthoritativeEvent with event_id "{event_id}", event_type '
        '"{event_type}", target_entity_id "{target_id}", jurisdiction_iso '
        '"{iso}", event_date "{event_date}", status "{status}", '
        'verbatim_summary "{summary}", and valid user_verified_snapshot provenance'
    )
)
def given_user_event(
    ctx: dict[str, Any],
    event_id: str,
    event_type: str,
    target_id: str,
    iso: str,
    event_date: str,
    status: str,
    summary: str,
) -> None:
    ctx["event"] = AuthoritativeEvent(
        event_id=event_id,
        event_type=event_type,  # type: ignore[arg-type]
        target_entity_id=target_id,
        jurisdiction_iso=iso,
        event_date=date.fromisoformat(event_date),
        status=status,
        verbatim_summary=summary,
        provenance=ctx["user_provenance"],
    )


@given(parsers.parse('a valid AuthoritativeEvent with status "{status}"'))
def given_valid_event_status(ctx: dict[str, Any], status: str) -> None:
    ctx["event"] = AuthoritativeEvent(
        event_id="evt:valid:1",
        event_type="hygiene_audit",
        target_entity_id="actor:in:fssai:10013022000417",
        jurisdiction_iso="IN",
        event_date=date(2026, 4, 1),
        status=status,
        verbatim_summary="Summary.",
        provenance=ctx["official_provenance"],
    )


@given(
    parsers.parse(
        "a concrete offline adapter implementing BaseSourceAdapter for "
        'source_name "{source_name}" and jurisdiction_iso "{iso}"'
    )
)
def given_concrete_adapter_meta(
    ctx: dict[str, Any], source_name: str, iso: str
) -> None:
    ctx["adapter_source_name"] = source_name
    ctx["adapter_iso"] = iso


@given(
    "raw fixture bytes containing one valid recall record with valid provenance "
    "and one ambiguous record missing content_sha256 and target_entity_id"
)
def given_raw_fixture_bytes(ctx: dict[str, Any]) -> None:
    fixture = [
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
                "retrieved_at": "2026-04-01T10:00:00+00:00",
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
            "verbatim_summary": "Missing target and sha256.",
            "provenance": {
                "source_url": "https://foscos.fssai.gov.in/recalls",
                "retrieved_at": "2026-04-01T10:00:00+00:00",
                "verification_tier": "official_registry",
            },
        },
    ]
    raw = json.dumps(fixture).encode("utf-8")
    ctx["adapter"] = _FixtureRecallAdapter(
        ctx["adapter_source_name"], ctx["adapter_iso"], raw
    )


@when(
    parsers.parse('I attempt to create an AuthoritativeEvent with event_type "{etype}"')
)
def attempt_invalid_event_type(ctx: dict[str, Any], etype: str) -> None:
    try:
        AuthoritativeEvent(
            event_id="evt:bad",
            event_type=etype,  # type: ignore[arg-type]
            target_entity_id="actor:in:fssai:10013022000417",
            jurisdiction_iso="IN",
            event_date=date(2026, 4, 1),
            status="Active",
            verbatim_summary="Bad.",
            provenance=ctx["official_provenance"],
        )
    except ValidationError as exc:
        ctx["error"] = exc


@when("I attempt to mutate its status field")
def mutate_status(ctx: dict[str, Any]) -> None:
    try:
        ctx["event"].status = "Cleared"
    except ValidationError as exc:
        ctx["error"] = exc


@when("I inspect BaseSourceAdapter")
def inspect_adapter(ctx: dict[str, Any]) -> None:
    ctx["adapter_cls"] = BaseSourceAdapter


@when("I run fetch(), parse(raw), and validate_and_emit(records)")
def run_adapter_pipeline(ctx: dict[str, Any]) -> None:
    adapter: _FixtureRecallAdapter = ctx["adapter"]
    raw = adapter.fetch()
    records = adapter.parse(raw)
    ctx["emitted"] = adapter.validate_and_emit(records)


@then("the AuthoritativeEvent is valid")
def check_event_valid(ctx: dict[str, Any]) -> None:
    assert isinstance(ctx["event"], AuthoritativeEvent)


@then(parsers.parse('its event_type is "{etype}"'))
def check_event_type(ctx: dict[str, Any], etype: str) -> None:
    assert ctx["event"].event_type == etype


@then(parsers.parse('its status is "{status}"'))
def check_status(ctx: dict[str, Any], status: str) -> None:
    assert ctx["event"].status == status


@then(parsers.parse('its batch_or_lot_no is "{lot}"'))
def check_lot(ctx: dict[str, Any], lot: str) -> None:
    assert ctx["event"].batch_or_lot_no == lot


@then("its batch_or_lot_no is null")
def check_lot_null(ctx: dict[str, Any]) -> None:
    assert ctx["event"].batch_or_lot_no is None


@then("a ValidationError is raised")
def check_validation_error(ctx: dict[str, Any]) -> None:
    assert isinstance(ctx["error"], ValidationError)


@then("it defines abstract methods fetch, parse, and validate_and_emit")
def check_abstract_methods(ctx: dict[str, Any]) -> None:
    cls = ctx["adapter_cls"]
    assert inspect.isabstract(cls)
    assert {"fetch", "parse", "validate_and_emit"}.issubset(cls.__abstractmethods__)


@then("attempting to instantiate BaseSourceAdapter directly raises TypeError")
def check_cannot_instantiate(ctx: dict[str, Any]) -> None:
    with pytest.raises(TypeError):
        ctx["adapter_cls"]()


@then(parsers.parse("{count:d} valid AuthoritativeEvent model is emitted"))
def check_emitted_count(ctx: dict[str, Any], count: int) -> None:
    assert len(ctx["emitted"]) == count
    assert all(isinstance(item, AuthoritativeEvent) for item in ctx["emitted"])


@then(
    "the ambiguous record is quarantined rather than guessed or coerced into "
    "a live entity"
)
def check_quarantined(ctx: dict[str, Any]) -> None:
    adapter: _FixtureRecallAdapter = ctx["adapter"]
    assert len(adapter.quarantined) == 1
    assert adapter.quarantined[0]["event_id"] == "evt:foscos:recall:ambiguous"
