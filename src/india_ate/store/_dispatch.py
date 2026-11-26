"""Entity-to-SQL dispatch helper for atomic batch persistence."""

from collections.abc import Callable

from pydantic import BaseModel

from india_ate.models import (
    AuthoritativeEvent,
    BrandListing,
    FoodItem,
    FoodPremises,
    ScientificStandard,
    Substance,
)
from india_ate.store._params import (
    brand_listing_params,
    event_params,
    food_item_params,
    premises_params,
    scientific_standard_params,
    substance_params,
)
from india_ate.store._schema import (
    INSERT_BRAND_LISTING_SQL,
    INSERT_EVENT_SQL,
    INSERT_FOOD_ITEM_SQL,
    INSERT_PREMISES_SQL,
    INSERT_STANDARD_SQL,
    INSERT_SUBSTANCE_SQL,
)

_DISPATCH_TABLE: dict[
    type[BaseModel], tuple[str, Callable[..., tuple[object, ...]]]
] = {
    FoodPremises: (INSERT_PREMISES_SQL, premises_params),
    BrandListing: (INSERT_BRAND_LISTING_SQL, brand_listing_params),
    AuthoritativeEvent: (INSERT_EVENT_SQL, event_params),
    FoodItem: (INSERT_FOOD_ITEM_SQL, food_item_params),
    Substance: (INSERT_SUBSTANCE_SQL, substance_params),
    ScientificStandard: (INSERT_STANDARD_SQL, scientific_standard_params),
}


def entity_insert_spec(entity: BaseModel) -> tuple[str, tuple[object, ...]] | None:
    """Return parameterized (SQL, params) for a canonical entity, or None."""
    entry = _DISPATCH_TABLE.get(type(entity))
    if entry is None:
        return None
    sql, builder = entry
    return sql, builder(entity)
