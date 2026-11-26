"""Food item model linked to FoodOn, IFCT 2017, GTIN, and supply-chain actors."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

ItemKind = Literal["raw_staple", "packaged_product", "menu_dish", "supplement"]


class FoodItem(BaseModel):
    """Canonical food product, staple, dish, or supplement."""

    model_config = ConfigDict(strict=True, frozen=True)

    item_id: str
    canonical_name: str
    item_kind: ItemKind
    foodon_uri: str | None = None
    ifct_code: str | None = None
    gtin_barcode: str | None = None
    manufacturer_premises_ids: list[str] = Field(default_factory=list)
    marketer_actor_ids: list[str] = Field(default_factory=list)
