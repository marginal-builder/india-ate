"""Unit tests for EvidenceProvenance, FoodActor, FoodPremises, and BrandListing."""

from datetime import UTC, datetime

import pytest
from pydantic import HttpUrl, ValidationError

from india_ate.models.actors import (
    BrandListing,
    FoodActor,
    FoodPremises,
    group_brand_listings_by_premises,
)
from india_ate.models.base import EvidenceProvenance


def test_evidence_provenance_valid(official_provenance: EvidenceProvenance) -> None:
    assert official_provenance.verification_tier == "official_registry"


def test_evidence_provenance_rejects_invalid_tier_and_url() -> None:
    with pytest.raises(ValidationError):
        EvidenceProvenance(
            source_name="Bad",
            source_url=HttpUrl("https://example.com"),
            retrieved_at=datetime(2026, 4, 1, 10, 0, tzinfo=UTC),
            content_sha256="abc",
            verification_tier="social_media_rumor",  # type: ignore[arg-type]
        )
    with pytest.raises(ValidationError):
        EvidenceProvenance(
            source_name="Bad URL",
            source_url="not-a-valid-url",  # type: ignore[arg-type]
            retrieved_at=datetime(2026, 4, 1, 10, 0, tzinfo=UTC),
            content_sha256="abc",
            verification_tier="official_registry",
        )


def test_evidence_provenance_strict_and_frozen(
    official_provenance: EvidenceProvenance,
) -> None:
    with pytest.raises(ValidationError):
        official_provenance.content_sha256 = "other"  # type: ignore[misc]
    with pytest.raises(ValidationError):
        EvidenceProvenance(
            source_name=123,  # type: ignore[arg-type]
            source_url=HttpUrl("https://example.com"),
            retrieved_at=datetime(2026, 4, 1, 10, 0, tzinfo=UTC),
            content_sha256="abc",
            verification_tier="official_registry",
        )


def test_food_actor_and_premises_liskov(
    sample_actor: FoodActor,
    sample_premises: FoodPremises,
    official_provenance: EvidenceProvenance,
) -> None:
    assert len(sample_actor.regulatory_ids) == 1
    assert isinstance(sample_premises, FoodActor)
    assert sample_premises.premises_type == "cloud_kitchen"

    minimal = FoodPremises(
        entity_id="actor:in:fssai:10013022000417",
        legal_name="Minimal Dark Store",
        jurisdiction_iso="IN",
        provenance=[official_provenance],
        premises_type="dark_store",
    )
    assert minimal.address is None
    assert minimal.postal_code is None
    assert minimal.city is None
    assert minimal.state is None
    assert minimal.lat is None
    assert minimal.lon is None


def test_reject_invalid_premises_type(official_provenance: EvidenceProvenance) -> None:
    with pytest.raises(ValidationError):
        FoodPremises(
            entity_id="actor:in:fssai:10013022000417",
            legal_name="Pushcart",
            jurisdiction_iso="IN",
            provenance=[official_provenance],
            premises_type="unlicensed_pushcart",  # type: ignore[arg-type]
        )


def test_brand_listing_grouping_and_validation(
    official_provenance: EvidenceProvenance,
) -> None:
    ts = datetime(2026, 4, 1, 9, 0, tzinfo=UTC)
    listings = [
        BrandListing(
            listing_id="listing:swiggy:101",
            display_name="Royal Biryani Kitchen",
            platform="swiggy",
            premises_entity_id="actor:in:fssai:23624001000123",
            postal_code="500081",
            first_seen_at=ts,
            last_seen_at=ts,
            provenance=official_provenance,
        ),
        BrandListing(
            listing_id="listing:zomato:202",
            display_name="Midnight Bowl Co",
            platform="zomato",
            premises_entity_id="actor:in:fssai:23624001000123",
            postal_code="500081",
            first_seen_at=ts,
            last_seen_at=ts,
            provenance=official_provenance,
        ),
        BrandListing(
            listing_id="listing:swiggy:303",
            display_name="Nawab Express",
            platform="swiggy",
            premises_entity_id="actor:in:fssai:23624001000123",
            postal_code="500081",
            first_seen_at=ts,
            last_seen_at=ts,
            provenance=official_provenance,
        ),
    ]
    grouped = group_brand_listings_by_premises(listings)
    assert (
        len({item.display_name for item in grouped["actor:in:fssai:23624001000123"]})
        == 3
    )

    with pytest.raises(ValidationError):
        BrandListing(
            listing_id="listing:bad:1",
            display_name="Bad",
            platform="unknown_delivery_app",  # type: ignore[arg-type]
            premises_entity_id="actor:in:fssai:23624001000123",
            first_seen_at=ts,
            last_seen_at=ts,
            provenance=official_provenance,
        )


def test_actor_premises_listing_immutability_and_strictness(
    sample_actor: FoodActor,
    sample_premises: FoodPremises,
    sample_brand_listing: BrandListing,
    official_provenance: EvidenceProvenance,
) -> None:
    with pytest.raises(ValidationError):
        sample_actor.legal_name = "Other"  # type: ignore[misc]
    with pytest.raises(ValidationError):
        sample_premises.premises_type = "restaurant"  # type: ignore[misc]
    with pytest.raises(ValidationError):
        sample_brand_listing.display_name = "Other"  # type: ignore[misc]
    ts = datetime(2026, 4, 1, 9, 0, tzinfo=UTC)
    with pytest.raises(ValidationError):
        BrandListing(
            listing_id="listing:swiggy:999",
            display_name=999,  # type: ignore[arg-type]
            platform="swiggy",
            premises_entity_id="actor:in:fssai:23624001000123",
            first_seen_at=ts,
            last_seen_at=ts,
            provenance=official_provenance,
        )
