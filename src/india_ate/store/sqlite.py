"""Parameterized SQLite runtime persistence store for india-ate."""

import sqlite3
from pathlib import Path
from typing import Self

from pydantic import BaseModel, ConfigDict

from india_ate.models import (
    AuthoritativeEvent,
    BrandListing,
    FoodPremises,
    IngestionBatch,
    QuarantinedRecord,
)
from india_ate.store._dispatch import entity_insert_spec
from india_ate.store._params import (
    brand_listing_params,
    event_params,
    premises_params,
    quarantined_params,
)
from india_ate.store._schema import (
    INSERT_BRAND_LISTING_SQL,
    INSERT_EVENT_SQL,
    INSERT_PREMISES_SQL,
    INSERT_QUARANTINED_SQL,
    SCHEMA_SQL,
)
from india_ate.store._science import ScienceStoreMixin

_OPTIONAL_PREMISES_FIELDS = (
    "address",
    "postal_code",
    "city",
    "state",
    "lat",
    "lon",
)


def _dedup_merge[T](existing: list[T], incoming: list[T]) -> list[T]:
    merged = list(existing)
    for item in incoming:
        if item not in merged:
            merged.append(item)
    return merged


def _merge_premises(existing: FoodPremises, incoming: FoodPremises) -> FoodPremises:
    updates: dict[str, object] = {
        "provenance": _dedup_merge(existing.provenance, incoming.provenance),
        "regulatory_ids": _dedup_merge(
            existing.regulatory_ids, incoming.regulatory_ids
        ),
    }
    for field in _OPTIONAL_PREMISES_FIELDS:
        if getattr(incoming, field) is None:
            existing_val = getattr(existing, field)
            if existing_val is not None:
                updates[field] = existing_val
    return incoming.model_copy(update=updates)


class GhostBrandCluster(BaseModel):
    """Physical FoodPremises and all BrandListings mapped to its FSSAI ID."""

    model_config = ConfigDict(strict=True, frozen=True)

    premises: FoodPremises
    listings: list[BrandListing]


class SQLiteStore(ScienceStoreMixin):
    """Parameterized raw sqlite3 store for all canonical entity layers."""

    def __init__(self, db_path: str | Path = ":memory:") -> None:
        self._db_path = str(db_path)
        if self._db_path != ":memory:":
            Path(self._db_path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self._db_path)

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def close(self) -> None:
        """Close the underlying SQLite connection."""
        self._conn.close()

    def initialize(self) -> None:
        """Create schema tables and indexes idempotently."""
        self._conn.executescript(SCHEMA_SQL)
        self._conn.commit()

    def _execute_write(self, sql: str, params: tuple[object, ...]) -> None:
        self._conn.execute(sql, params)
        self._conn.commit()

    def _fetch_one_model[ModelT: BaseModel](
        self, model_cls: type[ModelT], sql: str, param: str
    ) -> ModelT | None:
        row = self._conn.execute(sql, (param,)).fetchone()
        return model_cls.model_validate_json(row[0]) if row is not None else None

    def _fetch_many_models[ModelT: BaseModel](
        self, model_cls: type[ModelT], sql: str, params: tuple[object, ...] = ()
    ) -> list[ModelT]:
        rows = self._conn.execute(sql, params).fetchall()
        return [model_cls.model_validate_json(row[0]) for row in rows]

    def _upsert_premises(self, premises: FoodPremises) -> None:
        existing = self.get_premises_by_entity_id(premises.entity_id)
        merged = (
            _merge_premises(existing, premises) if existing is not None else premises
        )
        self._conn.execute(INSERT_PREMISES_SQL, premises_params(merged))

    def save_premises(self, premises: FoodPremises) -> None:
        """Insert or merge a FoodPremises record, preserving provenance and fields."""
        with self._conn:
            self._upsert_premises(premises)

    def get_premises_by_entity_id(self, entity_id: str) -> FoodPremises | None:
        """Retrieve a FoodPremises by its canonical entity_id."""
        sql = "SELECT payload_json FROM food_premises WHERE entity_id = ?"
        return self._fetch_one_model(FoodPremises, sql, entity_id)

    def get_premises_by_fssai_id(self, fssai_id: str) -> FoodPremises | None:
        """Retrieve a FoodPremises by its 14-digit FSSAI ID."""
        sql = "SELECT payload_json FROM food_premises WHERE fssai_id = ?"
        return self._fetch_one_model(FoodPremises, sql, fssai_id)

    def save_brand_listing(self, listing: BrandListing) -> None:
        """Insert or replace a BrandListing record."""
        self._execute_write(INSERT_BRAND_LISTING_SQL, brand_listing_params(listing))

    def get_brand_listings_for_premises(
        self, premises_entity_id: str
    ) -> list[BrandListing]:
        """Retrieve all BrandListings linked to a premises_entity_id."""
        sql = (
            "SELECT payload_json FROM brand_listings "
            "WHERE premises_entity_id = ? ORDER BY listing_id"
        )
        return self._fetch_many_models(BrandListing, sql, (premises_entity_id,))

    def save_event(self, event: AuthoritativeEvent) -> None:
        """Insert or replace an AuthoritativeEvent record."""
        self._execute_write(INSERT_EVENT_SQL, event_params(event))

    def get_events_for_target(self, target_entity_id: str) -> list[AuthoritativeEvent]:
        """Retrieve all AuthoritativeEvents targeting an entity_id."""
        sql = (
            "SELECT payload_json FROM authoritative_events "
            "WHERE target_entity_id = ? ORDER BY event_id"
        )
        return self._fetch_many_models(AuthoritativeEvent, sql, (target_entity_id,))

    def save_ingestion_batch(self, batch: IngestionBatch) -> None:
        """Persist entities and quarantined records atomically in one transaction."""
        with self._conn:
            for entity in batch.entities:
                if isinstance(entity, FoodPremises):
                    self._upsert_premises(entity)
                    continue
                spec = entity_insert_spec(entity)
                if spec is not None:
                    self._conn.execute(spec[0], spec[1])
            for record in batch.quarantined:
                self._conn.execute(INSERT_QUARANTINED_SQL, quarantined_params(record))

    def list_quarantined(
        self, source_name: str | None = None
    ) -> list[QuarantinedRecord]:
        """List quarantined records, optionally filtered by source_name."""
        if source_name is not None:
            sql = (
                "SELECT payload_json FROM quarantined_records "
                "WHERE source_name = ? ORDER BY id"
            )
            return self._fetch_many_models(QuarantinedRecord, sql, (source_name,))
        sql = "SELECT payload_json FROM quarantined_records ORDER BY id"
        return self._fetch_many_models(QuarantinedRecord, sql)

    def query_ghost_brand_cluster(self, fssai_id: str) -> GhostBrandCluster | None:
        """Query the physical premises and all brand listings for an FSSAI ID."""
        premises = self.get_premises_by_fssai_id(fssai_id)
        if premises is None:
            return None
        listings = self.get_brand_listings_for_premises(premises.entity_id)
        return GhostBrandCluster(premises=premises, listings=listings)

    def query_nearby_premises(self, postal_code: str) -> list[FoodPremises]:
        """Query all FoodPremises in a given postal_code."""
        sql = (
            "SELECT payload_json FROM food_premises "
            "WHERE postal_code = ? ORDER BY entity_id"
        )
        return self._fetch_many_models(FoodPremises, sql, (postal_code,))
