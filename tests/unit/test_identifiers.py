"""Unit tests for RegulatoryIdentifier and IndiaFSSAI14 offline decoder."""

import pytest
from pydantic import ValidationError

from india_ate.models.actors import FoodActor
from india_ate.models.base import EvidenceProvenance, RegulatoryIdentifier
from india_ate.models.identifiers import IndiaFSSAI14


def test_base_regulatory_identifier_raises_not_implemented() -> None:
    ident = RegulatoryIdentifier(
        jurisdiction_iso="US",
        scheme="US_FDA_FEI",
        raw_value="3001234567",
    )
    with pytest.raises(NotImplementedError):
        ident.decode_offline()


def test_india_fssai14_defaults() -> None:
    ident = IndiaFSSAI14(raw_value="10013022000417")
    assert ident.jurisdiction_iso == "IN"
    assert ident.scheme == "IN_FSSAI_14"


def test_decode_central_license_maharashtra_ro_mumbai() -> None:
    result = IndiaFSSAI14(raw_value="10013022000417").decode_offline()
    assert result == {
        "tier": "license",
        "pre_inspection_exempt_post_apr2026": False,
        "authority_scope": "central",
        "state_code": "00",
        "state_name": "Central",
        "registration_year": 2013,
        "officer_code": "022",
        "central_regional_office": "RO Mumbai",
        "officer_jurisdiction_state": "Maharashtra",
        "serial": "000417",
    }


def test_decode_bihar_state_license() -> None:
    result = IndiaFSSAI14(raw_value="10411012000075").decode_offline()
    assert result["tier"] == "license"
    assert result["pre_inspection_exempt_post_apr2026"] is False
    assert result["authority_scope"] == "state_or_ut"
    assert result["state_code"] == "04"
    assert result["state_name"] == "Bihar"
    assert result["registration_year"] == 2011
    assert result["officer_code"] == "012"
    assert result["central_regional_office"] is None
    assert result["officer_jurisdiction_state"] is None
    assert result["serial"] == "000075"


def test_decode_up_basic_registration() -> None:
    result = IndiaFSSAI14(raw_value="22711126011608").decode_offline()
    assert result["tier"] == "basic_registration"
    assert result["pre_inspection_exempt_post_apr2026"] is True
    assert result["authority_scope"] == "state_or_ut"
    assert result["state_code"] == "27"
    assert result["state_name"] == "Uttar Pradesh"
    assert result["registration_year"] == 2011
    assert result["officer_code"] == "126"
    assert result["central_regional_office"] is None
    assert result["serial"] == "011608"


def test_decode_central_jharkhand_ro_kolkata() -> None:
    result = IndiaFSSAI14(raw_value="10011034002374").decode_offline()
    assert result["central_regional_office"] == "RO Kolkata"
    assert result["officer_jurisdiction_state"] == "Jharkhand"
    assert result["serial"] == "002374"


def test_decode_central_chennai_and_guwahati() -> None:
    chennai = IndiaFSSAI14(raw_value="10020042000001").decode_offline()
    assert chennai["central_regional_office"] == "RO Chennai"
    assert chennai["officer_jurisdiction_state"] == "Tamil Nadu"

    guwahati = IndiaFSSAI14(raw_value="10020071000001").decode_offline()
    assert guwahati["central_regional_office"] == "RO Guwahati"
    assert guwahati["officer_jurisdiction_state"] == "Assam"


def test_decode_post_2011_states_telangana_and_ladakh() -> None:
    ts = IndiaFSSAI14(raw_value="23624001000123").decode_offline()
    assert ts["state_code"] == "36"
    assert ts["state_name"] == "Telangana"
    assert ts["registration_year"] == 2024

    la = IndiaFSSAI14(raw_value="13724001000456").decode_offline()
    assert la["state_code"] == "37"
    assert la["state_name"] == "Ladakh"


def test_decode_trims_whitespace() -> None:
    result = IndiaFSSAI14(raw_value=" 10013022000417 ").decode_offline()
    assert result["tier"] == "license"
    assert result["state_code"] == "00"
    assert result["serial"] == "000417"


@pytest.mark.parametrize(
    ("raw", "expected_substr"),
    [
        ("12345", "14-digit"),
        ("1001302200041A", "14-digit"),
        ("30013022000417", "tier"),
        ("13824001000001", "state"),
    ],
)
def test_decode_rejects_invalid_inputs(raw: str, expected_substr: str) -> None:
    ident = IndiaFSSAI14(raw_value=raw)
    with pytest.raises(ValueError, match=expected_substr):
        ident.decode_offline()


def test_india_fssai14_frozen_and_strict() -> None:
    ident = IndiaFSSAI14(raw_value="10013022000417")
    with pytest.raises(ValidationError):
        ident.raw_value = "22711126011608"  # type: ignore[misc]
    with pytest.raises(ValidationError):
        IndiaFSSAI14(raw_value=10013022000417)  # type: ignore[arg-type]


def test_regulatory_identifier_json_roundtrip_preserves_subclass(
    official_provenance: EvidenceProvenance,
) -> None:
    actor = FoodActor(
        entity_id="actor:in:fssai:10013022000417",
        legal_name="Acme Foods Pvt Ltd",
        jurisdiction_iso="IN",
        regulatory_ids=[IndiaFSSAI14(raw_value="10013022000417")],
        provenance=[official_provenance],
    )
    reconstructed = FoodActor.model_validate_json(actor.model_dump_json())
    assert isinstance(reconstructed.regulatory_ids[0], IndiaFSSAI14)
    assert reconstructed == actor
