"""Unit tests for Substance model."""

import pytest
from pydantic import ValidationError

from india_ate.models.substance import Substance, SubstanceClass


@pytest.mark.parametrize(
    ("substance_id", "name", "substance_class", "cas_number"),
    [
        ("substance:cas:50-81-7", "Ascorbic acid", "nutrient", "50-81-7"),
        ("substance:cas:532-32-1", "Sodium Benzoate", "additive", "532-32-1"),
        ("substance:cas:2921-88-2", "Chlorpyrifos", "pesticide_residue", "2921-88-2"),
        ("substance:cas:7439-92-1", "Lead", "heavy_metal", "7439-92-1"),
        ("substance:cas:1162-65-8", "Aflatoxin B1", "mycotoxin", "1162-65-8"),
        ("substance:bio:salmonella", "Salmonella spp.", "microbe", None),
        ("substance:allergen:peanut", "Peanut protein", "allergen", None),
    ],
)
def test_substance_categories(
    substance_id: str,
    name: str,
    substance_class: SubstanceClass,
    cas_number: str | None,
) -> None:
    s = Substance(
        substance_id=substance_id,
        canonical_name=name,
        substance_class=substance_class,
        cas_number=cas_number,
    )
    assert s.substance_class == substance_class


def test_substance_optional_defaults_and_validation(
    sample_substance: Substance,
) -> None:
    gluten = Substance(
        substance_id="substance:allergen:gluten",
        canonical_name="Gluten",
        substance_class="allergen",
    )
    assert gluten.cas_number is None
    assert gluten.pubchem_cid is None
    assert gluten.ins_e_number is None

    with pytest.raises(ValidationError):
        Substance(
            substance_id="substance:bad",
            canonical_name="Unknown",
            substance_class="unknown_chemical_group",  # type: ignore[arg-type]
        )
    with pytest.raises(ValidationError):
        sample_substance.cas_number = "000-00-0"  # type: ignore[misc]
    with pytest.raises(ValidationError):
        Substance(
            substance_id="substance:bad:2",
            canonical_name="Bad CAS",
            substance_class="additive",
            cas_number=532,  # type: ignore[arg-type]
        )
