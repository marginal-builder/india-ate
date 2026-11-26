"""Shared pytest fixtures for india-ate unit and acceptance tests."""

from datetime import UTC, date, datetime

import pytest
from pydantic import HttpUrl

from india_ate.models import (
    AuthoritativeEvent,
    BrandListing,
    EvidenceProvenance,
    FoodActor,
    FoodItem,
    FoodPremises,
    IndiaFSSAI14,
    ScientificStandard,
    Substance,
)

SAMPLE_SHA256 = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"


@pytest.fixture
def official_provenance() -> EvidenceProvenance:
    """Return a valid official_registry EvidenceProvenance fixture."""
    return EvidenceProvenance(
        source_name="FoSCoS Recall Portal",
        source_url=HttpUrl("https://foscos.fssai.gov.in/recalls"),
        retrieved_at=datetime(2026, 4, 1, 10, 0, tzinfo=UTC),
        content_sha256=SAMPLE_SHA256,
        verification_tier="official_registry",
    )


@pytest.fixture
def science_provenance() -> EvidenceProvenance:
    """Return a valid peer_reviewed_science EvidenceProvenance fixture."""
    return EvidenceProvenance(
        source_name="EFSA OpenFoodTox",
        source_url=HttpUrl(
            "https://www.efsa.europa.eu/en/data-report/chemical-hazards-data"
        ),
        retrieved_at=datetime(2026, 4, 1, 10, 0, tzinfo=UTC),
        content_sha256=SAMPLE_SHA256,
        verification_tier="peer_reviewed_science",
    )


@pytest.fixture
def user_provenance() -> EvidenceProvenance:
    """Return a valid user_verified_snapshot EvidenceProvenance fixture."""
    return EvidenceProvenance(
        source_name="Consumer Snap Snapshot",
        source_url=HttpUrl("https://foscos.fssai.gov.in/consumergrievance"),
        retrieved_at=datetime(2026, 4, 5, 12, 0, tzinfo=UTC),
        content_sha256=SAMPLE_SHA256,
        verification_tier="user_verified_snapshot",
    )


@pytest.fixture
def sample_actor(official_provenance: EvidenceProvenance) -> FoodActor:
    """Return a valid FoodActor fixture."""
    return FoodActor(
        entity_id="actor:in:fssai:10013022000417",
        legal_name="Acme Foods Pvt Ltd",
        jurisdiction_iso="IN",
        regulatory_ids=[IndiaFSSAI14(raw_value="10013022000417")],
        provenance=[official_provenance],
    )


@pytest.fixture
def sample_premises(official_provenance: EvidenceProvenance) -> FoodPremises:
    """Return a valid FoodPremises fixture."""
    return FoodPremises(
        entity_id="actor:in:fssai:23624001000123",
        legal_name="Deccan Cloud Hospitality",
        jurisdiction_iso="IN",
        regulatory_ids=[IndiaFSSAI14(raw_value="23624001000123")],
        provenance=[official_provenance],
        premises_type="cloud_kitchen",
        address="Plot 14, Madhapur",
        postal_code="500081",
        city="Hyderabad",
        state="Telangana",
        lat=17.4486,
        lon=78.3908,
    )


@pytest.fixture
def sample_brand_listing(official_provenance: EvidenceProvenance) -> BrandListing:
    """Return a valid BrandListing fixture."""
    return BrandListing(
        listing_id="listing:swiggy:101",
        display_name="Royal Biryani Kitchen",
        platform="swiggy",
        premises_entity_id="actor:in:fssai:23624001000123",
        postal_code="500081",
        first_seen_at=datetime(2026, 3, 1, 9, 0, tzinfo=UTC),
        last_seen_at=datetime(2026, 4, 1, 9, 0, tzinfo=UTC),
        provenance=official_provenance,
    )


@pytest.fixture
def sample_food_item() -> FoodItem:
    """Return a valid FoodItem fixture."""
    return FoodItem(
        item_id="item:ifct:E053",
        canonical_name="Turmeric powder",
        item_kind="raw_staple",
        foodon_uri="http://purl.obolibrary.org/obo/FOODON_03301414",
        ifct_code="E053",
    )


@pytest.fixture
def sample_substance() -> Substance:
    """Return a valid Substance fixture."""
    return Substance(
        substance_id="substance:cas:532-32-1",
        canonical_name="Sodium Benzoate",
        substance_class="additive",
        cas_number="532-32-1",
        pubchem_cid="517055",
        ins_e_number="INS 211",
    )


@pytest.fixture
def sample_standard(official_provenance: EvidenceProvenance) -> ScientificStandard:
    """Return a valid ScientificStandard fixture."""
    return ScientificStandard(
        standard_id="std:in:fssai:mrl:chlorpyrifos:turmeric",
        standard_type="statutory_mrl",
        jurisdiction_iso="IN",
        substance_id="substance:cas:2921-88-2",
        food_item_id="item:ifct:E053",
        value=0.05,
        unit="mg/kg",
        effective_date=date(2024, 1, 1),
        provenance=official_provenance,
    )


@pytest.fixture
def sample_event(official_provenance: EvidenceProvenance) -> AuthoritativeEvent:
    """Return a valid AuthoritativeEvent fixture."""
    return AuthoritativeEvent(
        event_id="evt:foscos:recall:2026-001",
        event_type="food_recall",
        target_entity_id="item:gtin:8901234567890",
        jurisdiction_iso="IN",
        event_date=date(2026, 3, 20),
        status="Initiated",
        batch_or_lot_no="LOT-MH-2026-09",
        verbatim_summary=(
            "Voluntary recall initiated due to elevated aflatoxin levels "
            "in batch LOT-MH-2026-09."
        ),
        provenance=official_provenance,
    )
