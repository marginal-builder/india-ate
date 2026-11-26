"""Food actor, physical premises, and brand listing entity models."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from india_ate.models.base import EvidenceProvenance, RegulatoryIdentifier

PremisesType = Literal[
    "cloud_kitchen",
    "dark_store",
    "restaurant",
    "co_packer_factory",
    "dairy_unit",
    "warehouse",
    "retail_vendor",
]

PlatformType = Literal[
    "swiggy",
    "zomato",
    "blinkit",
    "zepto",
    "instamart",
    "ondc",
    "packaged_retail",
]


class FoodActor(BaseModel):
    """Canonical legal food business actor."""

    model_config = ConfigDict(strict=True, frozen=True)

    entity_id: str
    legal_name: str
    jurisdiction_iso: str
    regulatory_ids: list[RegulatoryIdentifier] = Field(default_factory=list)
    provenance: list[EvidenceProvenance]


class FoodPremises(FoodActor):
    """Physical food premises substituting cleanly for FoodActor."""

    premises_type: PremisesType
    address: str | None = None
    postal_code: str | None = None
    city: str | None = None
    state: str | None = None
    lat: float | None = None
    lon: float | None = None


class BrandListing(BaseModel):
    """Maps consumer-facing storefront names N:1 to physical FoodPremises."""

    model_config = ConfigDict(strict=True, frozen=True)

    listing_id: str
    display_name: str
    platform: PlatformType
    premises_entity_id: str
    postal_code: str | None = None
    first_seen_at: datetime
    last_seen_at: datetime
    provenance: EvidenceProvenance


def group_brand_listings_by_premises(
    listings: list[BrandListing],
) -> dict[str, list[BrandListing]]:
    """Group BrandListing records by premises_entity_id to expose clusters."""
    grouped: dict[str, list[BrandListing]] = {}
    for listing in listings:
        grouped.setdefault(listing.premises_entity_id, []).append(listing)
    return grouped
