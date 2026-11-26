"""Acceptance tests for sqlite_store.feature."""

from collections.abc import Iterator
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from india_ate.models import (
    AuthoritativeEvent,
    BrandListing,
    EvidenceProvenance,
    FoodPremises,
    IndiaFSSAI14,
)
from india_ate.store import SQLiteStore

FEATURE_PATH = (
    Path(__file__).resolve().parents[2] / "features" / "store" / "sqlite_store.feature"
)
scenarios(str(FEATURE_PATH))


@pytest.fixture
def ctx(
    tmp_path: Path, official_provenance: EvidenceProvenance
) -> Iterator[dict[str, Any]]:
    state: dict[str, Any] = {
        "db_path": tmp_path / "test_store.db",
        "store": None,
        "provenance": official_provenance,
        "listings": [],
        "nearby": [],
    }
    yield state
    if state["store"] is not None:
        state["store"].close()


def _ensure_store(ctx: dict[str, Any]) -> SQLiteStore:
    if ctx["store"] is None:
        store = SQLiteStore(ctx["db_path"])
        store.initialize()
        ctx["store"] = store
    store_obj: SQLiteStore = ctx["store"]
    return store_obj


@given("an initialized SQLite store")
def given_init_store(ctx: dict[str, Any]) -> None:
    _ensure_store(ctx)


@given(
    parsers.parse('an initialized SQLite store with saved FoodPremises "{entity_id}"')
)
def given_store_with_premises(ctx: dict[str, Any], entity_id: str) -> None:
    store = _ensure_store(ctx)
    fssai = entity_id.split(":")[-1]
    premises = FoodPremises(
        entity_id=entity_id,
        legal_name="Saved Premises",
        jurisdiction_iso="IN",
        regulatory_ids=[IndiaFSSAI14(raw_value=fssai)],
        provenance=[ctx["provenance"]],
        premises_type="cloud_kitchen",
        postal_code="500081",
    )
    store.save_premises(premises)


@given(
    parsers.parse('an initialized SQLite store containing FoodPremises "{entity_id}"')
)
def given_store_containing_premises(ctx: dict[str, Any], entity_id: str) -> None:
    given_store_with_premises(ctx, entity_id)


@given(
    parsers.parse(
        'a FoodPremises with entity_id "{entity_id}", legal_name "{legal_name}", '
        'premises_type "{premises_type}", postal_code "{postal_code}", city '
        '"{city}", state "{state}", and IndiaFSSAI14 "{fssai}"'
    )
)
def given_full_premises(
    ctx: dict[str, Any],
    entity_id: str,
    legal_name: str,
    premises_type: str,
    postal_code: str,
    city: str,
    state: str,
    fssai: str,
) -> None:
    ctx["premises"] = FoodPremises(
        entity_id=entity_id,
        legal_name=legal_name,
        jurisdiction_iso="IN",
        regulatory_ids=[IndiaFSSAI14(raw_value=fssai)],
        provenance=[ctx["provenance"]],
        premises_type=premises_type,  # type: ignore[arg-type]
        postal_code=postal_code,
        city=city,
        state=state,
    )


@given(
    parsers.parse(
        'a FoodPremises with entity_id "{entity_id}", IndiaFSSAI14 "{fssai}", '
        'and postal_code "{postal_code}"'
    )
)
def given_cluster_premises(
    ctx: dict[str, Any], entity_id: str, fssai: str, postal_code: str
) -> None:
    store = _ensure_store(ctx)
    premises = FoodPremises(
        entity_id=entity_id,
        legal_name="Deccan Cloud",
        jurisdiction_iso="IN",
        regulatory_ids=[IndiaFSSAI14(raw_value=fssai)],
        provenance=[ctx["provenance"]],
        premises_type="cloud_kitchen",
        postal_code=postal_code,
    )
    store.save_premises(premises)
    ctx["premises"] = premises


@given(parsers.parse('a FoodPremises "{entity_id}" in postal_code "{postal_code}"'))
def given_nearby_premises(
    ctx: dict[str, Any], entity_id: str, postal_code: str
) -> None:
    store = _ensure_store(ctx)
    fssai = entity_id.split(":")[-1]
    premises = FoodPremises(
        entity_id=entity_id,
        legal_name=f"Premises {fssai}",
        jurisdiction_iso="IN",
        regulatory_ids=[IndiaFSSAI14(raw_value=fssai)],
        provenance=[ctx["provenance"]],
        premises_type="cloud_kitchen",
        postal_code=postal_code,
    )
    store.save_premises(premises)


@given(
    parsers.parse(
        'a BrandListing "{listing_id}" linked to premises_entity_id "{entity_id}"'
    )
)
def given_brand_listing(ctx: dict[str, Any], listing_id: str, entity_id: str) -> None:
    ts = datetime(2026, 4, 1, 9, 0, tzinfo=UTC)
    ctx["listing"] = BrandListing(
        listing_id=listing_id,
        display_name="Royal Biryani Kitchen",
        platform="swiggy",
        premises_entity_id=entity_id,
        postal_code="500081",
        first_seen_at=ts,
        last_seen_at=ts,
        provenance=ctx["provenance"],
    )


@given(
    parsers.parse(
        'an AuthoritativeEvent "{event_id}" targeting "{target_id}" with '
        'status "{status}"'
    )
)
def given_auth_event(
    ctx: dict[str, Any], event_id: str, target_id: str, status: str
) -> None:
    ctx["event"] = AuthoritativeEvent(
        event_id=event_id,
        event_type="enforcement_raid_or_suspension",
        target_entity_id=target_id,
        jurisdiction_iso="IN",
        event_date=date(2026, 4, 2),
        status=status,
        verbatim_summary="Suspended by state authority.",
        provenance=ctx["provenance"],
    )


@given(
    parsers.parse(
        '3 BrandListings ("{n1}", "{n2}", "{n3}") all linked to '
        'premises_entity_id "{entity_id}"'
    )
)
def given_three_listings(
    ctx: dict[str, Any], n1: str, n2: str, n3: str, entity_id: str
) -> None:
    store = _ensure_store(ctx)
    ts = datetime(2026, 4, 1, 9, 0, tzinfo=UTC)
    for idx, name in enumerate((n1, n2, n3), start=1):
        listing = BrandListing(
            listing_id=f"listing:cluster:{idx}",
            display_name=name,
            platform="swiggy",
            premises_entity_id=entity_id,
            postal_code="500081",
            first_seen_at=ts,
            last_seen_at=ts,
            provenance=ctx["provenance"],
        )
        store.save_brand_listing(listing)


@when("I save the FoodPremises to the SQLite store")
def save_premises(ctx: dict[str, Any]) -> None:
    _ensure_store(ctx).save_premises(ctx["premises"])


@when(parsers.parse('I get the FoodPremises by entity_id "{entity_id}"'))
def get_by_entity_id(ctx: dict[str, Any], entity_id: str) -> None:
    ctx["retrieved"] = _ensure_store(ctx).get_premises_by_entity_id(entity_id)


@when(parsers.parse('I get the FoodPremises by FSSAI ID "{fssai_id}"'))
def get_by_fssai_id(ctx: dict[str, Any], fssai_id: str) -> None:
    ctx["retrieved"] = _ensure_store(ctx).get_premises_by_fssai_id(fssai_id)


@when("I save the BrandListing and AuthoritativeEvent to the SQLite store")
def save_listing_and_event(ctx: dict[str, Any]) -> None:
    store = _ensure_store(ctx)
    store.save_brand_listing(ctx["listing"])
    store.save_event(ctx["event"])


@when(parsers.parse('I query the ghost-brand cluster for FSSAI ID "{fssai_id}"'))
def query_cluster(ctx: dict[str, Any], fssai_id: str) -> None:
    ctx["cluster"] = _ensure_store(ctx).query_ghost_brand_cluster(fssai_id)


@when(parsers.parse('I query nearby FoodPremises for postal_code "{postal_code}"'))
def query_nearby(ctx: dict[str, Any], postal_code: str) -> None:
    ctx["nearby"] = _ensure_store(ctx).query_nearby_premises(postal_code)


@then("the retrieved FoodPremises equals the saved FoodPremises")
def check_retrieved_equals(ctx: dict[str, Any]) -> None:
    assert ctx["retrieved"] == ctx["premises"]


@then(parsers.parse('its entity_id is "{entity_id}"'))
def check_entity_id(ctx: dict[str, Any], entity_id: str) -> None:
    assert ctx["retrieved"].entity_id == entity_id


@then(parsers.parse('its postal_code is "{postal_code}"'))
def check_postal_code(ctx: dict[str, Any], postal_code: str) -> None:
    assert ctx["retrieved"].postal_code == postal_code


@then(
    parsers.parse(
        'retrieving BrandListings for "{entity_id}" returns {count:d} listing '
        'with listing_id "{listing_id}"'
    )
)
def check_listings_for_premises(
    ctx: dict[str, Any], entity_id: str, count: int, listing_id: str
) -> None:
    listings = _ensure_store(ctx).get_brand_listings_for_premises(entity_id)
    assert len(listings) == count
    assert listings[0].listing_id == listing_id


@then(
    parsers.parse(
        'retrieving AuthoritativeEvents for "{entity_id}" returns {count:d} '
        'event with status "{status}"'
    )
)
def check_events_for_target(
    ctx: dict[str, Any], entity_id: str, count: int, status: str
) -> None:
    events = _ensure_store(ctx).get_events_for_target(entity_id)
    assert len(events) == count
    assert events[0].status == status


@then(parsers.parse('the cluster returns the FoodPremises "{entity_id}"'))
def check_cluster_premises(ctx: dict[str, Any], entity_id: str) -> None:
    assert ctx["cluster"] is not None
    assert ctx["cluster"].premises.entity_id == entity_id


@then(parsers.parse("the cluster contains all {count:d} BrandListings"))
def check_cluster_listings_count(ctx: dict[str, Any], count: int) -> None:
    assert len(ctx["cluster"].listings) == count


@then(parsers.parse("{count:d} FoodPremises records are returned"))
def check_nearby_count(ctx: dict[str, Any], count: int) -> None:
    assert len(ctx["nearby"]) == count


@then(parsers.parse('the returned entity_ids do not include "{entity_id}"'))
def check_nearby_excludes(ctx: dict[str, Any], entity_id: str) -> None:
    assert entity_id not in {p.entity_id for p in ctx["nearby"]}


@then("an empty result is returned without raising a database error")
def check_cluster_empty(ctx: dict[str, Any]) -> None:
    assert ctx["cluster"] is None


@then(parsers.parse('FoodPremises "{entity_id}" still exists in the SQLite store'))
def check_premises_still_exists(ctx: dict[str, Any], entity_id: str) -> None:
    assert _ensure_store(ctx).get_premises_by_entity_id(entity_id) is not None
