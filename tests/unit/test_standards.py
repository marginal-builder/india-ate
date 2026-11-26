"""Unit tests for ScientificStandard model."""

import pytest
from pydantic import ValidationError

from india_ate.models.base import EvidenceProvenance
from india_ate.models.standards import ScientificStandard, StandardType


@pytest.mark.parametrize(
    (
        "standard_id",
        "standard_type",
        "jurisdiction_iso",
        "substance_id",
        "value",
        "unit",
    ),
    [
        (
            "std:codex:adi:532-32-1",
            "toxicology_reference_limit",
            "WHO_CODEX",
            "substance:cas:532-32-1",
            5.0,
            "mg/kg",
        ),
        (
            "std:in:mrl:2921-88-2",
            "statutory_mrl",
            "IN",
            "substance:cas:2921-88-2",
            0.05,
            "mg/kg",
        ),
        (
            "std:in:ifct:E053:vitc",
            "nutrient_composition",
            "IN",
            "substance:cas:50-81-7",
            0.026,
            "g/100g",
        ),
        (
            "std:in:icmr:rda:vitc",
            "dietary_guideline",
            "IN",
            "substance:cas:50-81-7",
            80.0,
            "mg/day",
        ),
    ],
)
def test_scientific_standard_types(
    standard_id: str,
    standard_type: StandardType,
    jurisdiction_iso: str,
    substance_id: str,
    value: float,
    unit: str,
    science_provenance: EvidenceProvenance,
) -> None:
    std = ScientificStandard(
        standard_id=standard_id,
        standard_type=standard_type,
        jurisdiction_iso=jurisdiction_iso,
        substance_id=substance_id,
        value=value,
        unit=unit,
        provenance=science_provenance,
    )
    assert std.standard_type == standard_type
    assert std.food_item_id is None
    assert std.effective_date is None


def test_scientific_standard_strict_and_frozen(
    sample_standard: ScientificStandard,
    official_provenance: EvidenceProvenance,
) -> None:
    assert sample_standard.value == 0.05
    with pytest.raises(ValidationError):
        ScientificStandard(
            standard_id="std:bad",
            standard_type="opinion_score",  # type: ignore[arg-type]
            jurisdiction_iso="IN",
            substance_id="substance:cas:50-81-7",
            value=1.0,
            unit="mg/kg",
            provenance=official_provenance,
        )
    with pytest.raises(ValidationError):
        sample_standard.value = 1.0  # type: ignore[misc]
    with pytest.raises(ValidationError):
        ScientificStandard(
            standard_id="std:bad:2",
            standard_type="statutory_mrl",
            jurisdiction_iso="IN",
            substance_id="substance:cas:50-81-7",
            value="0.05",  # type: ignore[arg-type]
            unit="mg/kg",
            provenance=official_provenance,
        )
    with pytest.raises(ValidationError):
        ScientificStandard(  # type: ignore[call-arg]
            standard_id="std:bad:3",
            standard_type="statutory_mrl",
            jurisdiction_iso="IN",
            substance_id="substance:cas:50-81-7",
            value=0.05,
            unit="mg/kg",
        )
