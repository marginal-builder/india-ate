"""Substance model keyed by CAS, PubChem CID, and INS/E-number."""

from typing import Literal

from pydantic import BaseModel, ConfigDict

SubstanceClass = Literal[
    "nutrient",
    "additive",
    "pesticide_residue",
    "heavy_metal",
    "mycotoxin",
    "microbe",
    "allergen",
]


class Substance(BaseModel):
    """Canonical nutrient, additive, contaminant, microbe, or allergen."""

    model_config = ConfigDict(strict=True, frozen=True)

    substance_id: str
    canonical_name: str
    substance_class: SubstanceClass
    cas_number: str | None = None
    pubchem_cid: str | None = None
    ins_e_number: str | None = None
