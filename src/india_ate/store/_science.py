"""Science & nutrition SQLite persistence mixin for FoodItem, Substance, Standards."""

from pydantic import BaseModel

from india_ate.models import FoodItem, ScientificStandard, Substance
from india_ate.store._params import (
    food_item_params,
    scientific_standard_params,
    substance_params,
)
from india_ate.store._schema import (
    INSERT_FOOD_ITEM_SQL,
    INSERT_STANDARD_SQL,
    INSERT_SUBSTANCE_SQL,
)


class ScienceStoreMixin:
    """Mixin providing CRUD and query methods for science entities."""

    def _execute_write(self, sql: str, params: tuple[object, ...]) -> None:
        raise NotImplementedError

    def _fetch_one_model[ModelT: BaseModel](
        self, model_cls: type[ModelT], sql: str, param: str
    ) -> ModelT | None:
        raise NotImplementedError

    def _fetch_many_models[ModelT: BaseModel](
        self, model_cls: type[ModelT], sql: str, params: tuple[object, ...] = ()
    ) -> list[ModelT]:
        raise NotImplementedError

    def save_food_item(self, item: FoodItem) -> None:
        """Insert or replace a FoodItem record."""
        self._execute_write(INSERT_FOOD_ITEM_SQL, food_item_params(item))

    def get_food_item(self, item_id: str) -> FoodItem | None:
        """Retrieve a FoodItem by item_id."""
        sql = "SELECT payload_json FROM food_items WHERE item_id = ?"
        return self._fetch_one_model(FoodItem, sql, item_id)

    def search_food_items(self, query: str, limit: int = 25) -> list[FoodItem]:
        """Search FoodItems by case-insensitive canonical_name substring."""
        sql = (
            "SELECT payload_json FROM food_items "
            "WHERE canonical_name LIKE ? ORDER BY item_id LIMIT ?"
        )
        return self._fetch_many_models(FoodItem, sql, (f"%{query}%", limit))

    def save_substance(self, substance: Substance) -> None:
        """Insert or replace a Substance record."""
        self._execute_write(INSERT_SUBSTANCE_SQL, substance_params(substance))

    def get_substance(self, substance_id: str) -> Substance | None:
        """Retrieve a Substance by substance_id."""
        sql = "SELECT payload_json FROM substances WHERE substance_id = ?"
        return self._fetch_one_model(Substance, sql, substance_id)

    def save_scientific_standard(self, standard: ScientificStandard) -> None:
        """Insert or replace a ScientificStandard record."""
        self._execute_write(INSERT_STANDARD_SQL, scientific_standard_params(standard))

    def get_standards_for_food_item(
        self, food_item_id: str
    ) -> list[ScientificStandard]:
        """Retrieve all ScientificStandards linked to a food_item_id."""
        sql = (
            "SELECT payload_json FROM scientific_standards "
            "WHERE food_item_id = ? ORDER BY standard_id"
        )
        return self._fetch_many_models(ScientificStandard, sql, (food_item_id,))

    def get_standards_for_substance(
        self, substance_id: str
    ) -> list[ScientificStandard]:
        """Retrieve all ScientificStandards linked to a substance_id."""
        sql = (
            "SELECT payload_json FROM scientific_standards "
            "WHERE substance_id = ? ORDER BY standard_id"
        )
        return self._fetch_many_models(ScientificStandard, sql, (substance_id,))
