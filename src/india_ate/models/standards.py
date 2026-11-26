"""Scientific standard model for toxicology limits, MRLs, and nutrition."""

from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict

from india_ate.models.base import EvidenceProvenance

StandardType = Literal[
    "toxicology_reference_limit",
    "statutory_mrl",
    "nutrient_composition",
    "dietary_guideline",
]


class ScientificStandard(BaseModel):
    """Authoritative statutory limit, toxicology benchmark, or nutrient standard."""

    model_config = ConfigDict(strict=True, frozen=True)

    standard_id: str
    standard_type: StandardType
    jurisdiction_iso: str
    substance_id: str
    food_item_id: str | None = None
    value: float
    unit: str
    effective_date: date | None = None
    provenance: EvidenceProvenance
