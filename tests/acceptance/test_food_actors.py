"""Acceptance tests for food_actors.feature."""

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest
from pydantic import HttpUrl, ValidationError
from pytest_bdd import given, parsers, scenarios, then, when

from india_ate.models import (
    BrandListing,
    EvidenceProvenance,
    FoodActor,
    FoodPremises,
    IndiaFSSAI14,
    group_brand_listings_by_premises,
)

FEATURE_PATH = (
    Path(__file__).resolve().parents[2]
    / "features"
    / "entity_graph"
    / "food_actors.feature"
)
scenarios(str(FEATURE_PATH))


@pytest.fixture
def ctx(official_provenance: EvidenceProvenance) -> dict[str, Any]:
    return {
        "provenance": official_provenance,
        "listings": [],
        "error": None,
        "grouped": {},
    }


@given(
    parsers.parse(
        'an EvidenceProvenance with source_name "{source_name}", '
        'source_url "{source_url}", retrieved_at "{retrieved_at}", '
        'content_sha256 "{content_sha256}", and verification_tier '
        '"{verification_tier}"'
    )
)
def create_provenance(
    ctx: dict[str, Any],
    source_name: str,
    source_url: str,
    retrieved_at: str,
    content_sha256: str,
    verification_tier: str,
) -> None:
    ctx["provenance_model"] = EvidenceProvenance(
        source_name=source_name,
        source_url=HttpUrl(source_url),
        retrieved_at=datetime.fromisoformat(retrieved_at),
        content_sha256=content_sha256,
        verification_tier=verification_tier,  # type: ignore[arg-type]
    )


@then("the EvidenceProvenance is valid")
def provenance_is_valid(ctx: dict[str, Any]) -> None:
    assert isinstance(ctx["provenance_model"], EvidenceProvenance)


@then(parsers.parse('its verification_tier is "{tier}"'))
def check_provenance_tier(ctx: dict[str, Any], tier: str) -> None:
    assert ctx["provenance_model"].verification_tier == tier


@when(
    parsers.parse(
        'I attempt to create an EvidenceProvenance with verification_tier "{tier}"'
    )
)
def attempt_invalid_tier(ctx: dict[str, Any], tier: str) -> None:
    try:
        EvidenceProvenance(
            source_name="Test",
            source_url=HttpUrl("https://foscos.fssai.gov.in/recalls"),
            retrieved_at=datetime(2026, 4, 1, 10, 0, tzinfo=UTC),
            content_sha256="abc",
            verification_tier=tier,  # type: ignore[arg-type]
        )
    except ValidationError as exc:
        ctx["error"] = exc


@when(
    parsers.parse('I attempt to create an EvidenceProvenance with source_url "{url}"')
)
def attempt_invalid_url(ctx: dict[str, Any], url: str) -> None:
    try:
        EvidenceProvenance(
            source_name="Test",
            source_url=url,  # type: ignore[arg-type]
            retrieved_at=datetime(2026, 4, 1, 10, 0, tzinfo=UTC),
            content_sha256="abc",
            verification_tier="official_registry",
        )
    except ValidationError as exc:
        ctx["error"] = exc


@given("a valid EvidenceProvenance record")
def given_valid_provenance(
    ctx: dict[str, Any], official_provenance: EvidenceProvenance
) -> None:
    ctx["provenance_model"] = official_provenance


@when("I attempt to mutate its content_sha256 field")
def mutate_provenance_sha(ctx: dict[str, Any]) -> None:
    try:
        ctx["provenance_model"].content_sha256 = "tampered"
    except ValidationError as exc:
        ctx["error"] = exc


@when(
    parsers.parse(
        "I attempt to create an EvidenceProvenance with integer {num:d} as source_name"
    )
)
def attempt_int_source_name(ctx: dict[str, Any], num: int) -> None:
    try:
        EvidenceProvenance(
            source_name=num,  # type: ignore[arg-type]
            source_url=HttpUrl("https://foscos.fssai.gov.in/recalls"),
            retrieved_at=datetime(2026, 4, 1, 10, 0, tzinfo=UTC),
            content_sha256="abc",
            verification_tier="official_registry",
        )
    except ValidationError as exc:
        ctx["error"] = exc


@then("a ValidationError is raised")
def check_validation_error(ctx: dict[str, Any]) -> None:
    assert isinstance(ctx["error"], ValidationError)


@given(
    parsers.parse(
        'a FoodActor with entity_id "{entity_id}", legal_name "{legal_name}", '
        'jurisdiction_iso "{jurisdiction_iso}", regulatory_ids containing '
        'IndiaFSSAI14 "{raw_value}", and valid official_registry provenance'
    )
)
def create_actor(
    ctx: dict[str, Any],
    entity_id: str,
    legal_name: str,
    jurisdiction_iso: str,
    raw_value: str,
) -> None:
    ctx["actor"] = FoodActor(
        entity_id=entity_id,
        legal_name=legal_name,
        jurisdiction_iso=jurisdiction_iso,
        regulatory_ids=[IndiaFSSAI14(raw_value=raw_value)],
        provenance=[ctx["provenance"]],
    )


@then("the FoodActor is valid")
def check_actor_valid(ctx: dict[str, Any]) -> None:
    assert isinstance(ctx["actor"], FoodActor)


@then(parsers.parse("its regulatory_ids has length {length:d}"))
def check_reg_ids_len(ctx: dict[str, Any], length: int) -> None:
    assert len(ctx["actor"].regulatory_ids) == length


@then(parsers.parse("its provenance has length {length:d}"))
def check_prov_len(ctx: dict[str, Any], length: int) -> None:
    assert len(ctx["actor"].provenance) == length


@given(
    parsers.parse(
        'a FoodPremises with entity_id "{entity_id}", legal_name "{legal_name}", '
        'jurisdiction_iso "{jurisdiction_iso}", premises_type "{premises_type}", '
        'address "{address}", postal_code "{postal_code}", city "{city}", '
        'state "{state}", lat {lat:f}, lon {lon:f}, and valid provenance'
    )
)
def create_premises(
    ctx: dict[str, Any],
    entity_id: str,
    legal_name: str,
    jurisdiction_iso: str,
    premises_type: str,
    address: str,
    postal_code: str,
    city: str,
    state: str,
    lat: float,
    lon: float,
) -> None:
    ctx["premises"] = FoodPremises(
        entity_id=entity_id,
        legal_name=legal_name,
        jurisdiction_iso=jurisdiction_iso,
        premises_type=premises_type,  # type: ignore[arg-type]
        address=address,
        postal_code=postal_code,
        city=city,
        state=state,
        lat=lat,
        lon=lon,
        provenance=[ctx["provenance"]],
    )


@then("the FoodPremises is an instance of FoodActor")
def check_premises_liskov(ctx: dict[str, Any]) -> None:
    assert isinstance(ctx["premises"], FoodActor)


@then(parsers.parse('its premises_type is "{premises_type}"'))
def check_premises_type(ctx: dict[str, Any], premises_type: str) -> None:
    assert ctx["premises"].premises_type == premises_type


@then(parsers.parse('its postal_code is "{postal_code}"'))
def check_postal_code(ctx: dict[str, Any], postal_code: str) -> None:
    assert ctx["premises"].postal_code == postal_code


@when(parsers.parse('I attempt to create a FoodPremises with premises_type "{ptype}"'))
def attempt_invalid_premises_type(ctx: dict[str, Any], ptype: str) -> None:
    try:
        FoodPremises(
            entity_id="actor:in:fssai:10013022000417",
            legal_name="Test",
            jurisdiction_iso="IN",
            premises_type=ptype,  # type: ignore[arg-type]
            provenance=[ctx["provenance"]],
        )
    except ValidationError as exc:
        ctx["error"] = exc


@given(
    parsers.parse(
        'a FoodPremises with only required fields and premises_type "{ptype}"'
    )
)
def create_minimal_premises(ctx: dict[str, Any], ptype: str) -> None:
    ctx["premises"] = FoodPremises(
        entity_id="actor:in:fssai:10013022000417",
        legal_name="Minimal Store",
        jurisdiction_iso="IN",
        premises_type=ptype,  # type: ignore[arg-type]
        provenance=[ctx["provenance"]],
    )


@then("address is null")
def check_address_null(ctx: dict[str, Any]) -> None:
    assert ctx["premises"].address is None


@then("postal_code is null")
def check_postal_null(ctx: dict[str, Any]) -> None:
    assert ctx["premises"].postal_code is None


@then("city is null")
def check_city_null(ctx: dict[str, Any]) -> None:
    assert ctx["premises"].city is None


@then("state is null")
def check_state_null(ctx: dict[str, Any]) -> None:
    assert ctx["premises"].state is None


@then("lat is null")
def check_lat_null(ctx: dict[str, Any]) -> None:
    assert ctx["premises"].lat is None


@then("lon is null")
def check_lon_null(ctx: dict[str, Any]) -> None:
    assert ctx["premises"].lon is None


@given(
    parsers.parse(
        'a FoodPremises with entity_id "{entity_id}" and postal_code "{postal_code}"'
    )
)
def given_premises_short(ctx: dict[str, Any], entity_id: str, postal_code: str) -> None:
    ctx["premises"] = FoodPremises(
        entity_id=entity_id,
        legal_name="Deccan Cloud Hospitality",
        jurisdiction_iso="IN",
        premises_type="cloud_kitchen",
        postal_code=postal_code,
        provenance=[ctx["provenance"]],
    )


@given(
    parsers.parse(
        'a BrandListing "{listing_id}" with display_name "{display_name}", '
        'platform "{platform}", and premises_entity_id "{premises_entity_id}"'
    )
)
def given_brand_listing(
    ctx: dict[str, Any],
    listing_id: str,
    display_name: str,
    platform: str,
    premises_entity_id: str,
) -> None:
    ts = datetime(2026, 4, 1, 9, 0, tzinfo=UTC)
    ctx["listings"].append(
        BrandListing(
            listing_id=listing_id,
            display_name=display_name,
            platform=platform,  # type: ignore[arg-type]
            premises_entity_id=premises_entity_id,
            postal_code=ctx["premises"].postal_code,
            first_seen_at=ts,
            last_seen_at=ts,
            provenance=ctx["provenance"],
        )
    )


@when("I group those BrandListings by premises_entity_id")
def group_listings(ctx: dict[str, Any]) -> None:
    ctx["grouped"] = group_brand_listings_by_premises(ctx["listings"])


@then(
    parsers.parse(
        'premises_entity_id "{entity_id}" has {count:d} distinct storefront '
        "display names in its ghost-brand cluster"
    )
)
def check_cluster_count(ctx: dict[str, Any], entity_id: str, count: int) -> None:
    names = {item.display_name for item in ctx["grouped"][entity_id]}
    assert len(names) == count


@when(parsers.parse('I attempt to create a BrandListing with platform "{platform}"'))
def attempt_invalid_platform(ctx: dict[str, Any], platform: str) -> None:
    ts = datetime(2026, 4, 1, 9, 0, tzinfo=UTC)
    try:
        BrandListing(
            listing_id="listing:bad:1",
            display_name="Bad",
            platform=platform,  # type: ignore[arg-type]
            premises_entity_id="actor:in:fssai:23624001000123",
            first_seen_at=ts,
            last_seen_at=ts,
            provenance=ctx["provenance"],
        )
    except ValidationError as exc:
        ctx["error"] = exc


@given("a valid FoodActor, FoodPremises, and BrandListing")
def given_all_three(
    ctx: dict[str, Any],
    sample_actor: FoodActor,
    sample_premises: FoodPremises,
    sample_brand_listing: BrandListing,
) -> None:
    ctx["actor"] = sample_actor
    ctx["premises"] = sample_premises
    ctx["listing"] = sample_brand_listing


@when("I attempt to mutate legal_name on FoodActor")
def mutate_actor(ctx: dict[str, Any]) -> None:
    try:
        ctx["actor"].legal_name = "Other"
    except ValidationError as exc:
        ctx["error"] = exc


@when("I attempt to mutate premises_type on FoodPremises")
def mutate_premises(ctx: dict[str, Any]) -> None:
    try:
        ctx["premises"].premises_type = "restaurant"
    except ValidationError as exc:
        ctx["error"] = exc


@when("I attempt to mutate display_name on BrandListing")
def mutate_listing(ctx: dict[str, Any]) -> None:
    try:
        ctx["listing"].display_name = "Other"
    except ValidationError as exc:
        ctx["error"] = exc


@when(
    parsers.parse(
        "I attempt to create a BrandListing with integer {num:d} as display_name"
    )
)
def attempt_int_display_name(ctx: dict[str, Any], num: int) -> None:
    ts = datetime(2026, 4, 1, 9, 0, tzinfo=UTC)
    try:
        BrandListing(
            listing_id="listing:bad:2",
            display_name=num,  # type: ignore[arg-type]
            platform="swiggy",
            premises_entity_id="actor:in:fssai:23624001000123",
            first_seen_at=ts,
            last_seen_at=ts,
            provenance=ctx["provenance"],
        )
    except ValidationError as exc:
        ctx["error"] = exc
