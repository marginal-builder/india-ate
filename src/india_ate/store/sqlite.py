"""Parameterized SQLite runtime persistence store for india-ate."""

import sqlite3
from pathlib import Path
from typing import Self

from pydantic import BaseModel, ConfigDict

from india_ate.models import AuthoritativeEvent, BrandListing, FoodPremises
from india_ate.store._schema import (
    INSERT_BRAND_LISTING_SQL,
    INSERT_EVENT_SQL,
    INSERT_PREMISES_SQL,
    SCHEMA_SQL,
)

FSSAI_SCHEME = "IN_FSSAI_14"


class GhostBrandCluster(BaseModel):
    """Physical FoodPremises and all BrandListings mapped to its FSSAI ID."""

    model_config = ConfigDict(strict=True, frozen=True)

    premises: FoodPremises
    listings: list[BrandListing]


def _extract_fssai_id(premises: FoodPremises) -> str | None:
    for reg in premises.regulatory_ids:
        if reg.scheme == FSSAI_SCHEME:
            return reg.raw_value.strip()
    return None


class SQLiteStore:
    """Parameterized raw sqlite3 store for FoodPremises, BrandListing, and Events."""

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
        self, model_cls: type[ModelT], sql: str, param: str
    ) -> list[ModelT]:
        rows = self._conn.execute(sql, (param,)).fetchall()
        return [model_cls.model_validate_json(row[0]) for row in rows]

    def save_premises(self, premises: FoodPremises) -> None:
        """Insert or replace a FoodPremises record."""
        params = (
            premises.entity_id,
            premises.legal_name,
            premises.jurisdiction_iso,
            premises.premises_type,
            premises.address,
            premises.postal_code,
            premises.city,
            premises.state,
            premises.lat,
            premises.lon,
            _extract_fssai_id(premises),
            premises.model_dump_json(),
        )
        self._execute_write(INSERT_PREMISES_SQL, params)

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
        params = (
            listing.listing_id,
            listing.display_name,
            listing.platform,
            listing.premises_entity_id,
            listing.postal_code,
            listing.first_seen_at.isoformat(),
            listing.last_seen_at.isoformat(),
            listing.model_dump_json(),
        )
        self._execute_write(INSERT_BRAND_LISTING_SQL, params)

    def get_brand_listings_for_premises(
        self, premises_entity_id: str
    ) -> list[BrandListing]:
        """Retrieve all BrandListings linked to a premises_entity_id."""
        sql = (
            "SELECT payload_json FROM brand_listings "
            "WHERE premises_entity_id = ? ORDER BY listing_id"
        )
        return self._fetch_many_models(BrandListing, sql, premises_entity_id)

    def save_event(self, event: AuthoritativeEvent) -> None:
        """Insert or replace an AuthoritativeEvent record."""
        params = (
            event.event_id,
            event.event_type,
            event.target_entity_id,
            event.jurisdiction_iso,
            event.event_date.isoformat(),
            event.status,
            event.batch_or_lot_no,
            event.verbatim_summary,
            event.model_dump_json(),
        )
        self._execute_write(INSERT_EVENT_SQL, params)

    def get_events_for_target(self, target_entity_id: str) -> list[AuthoritativeEvent]:
        """Retrieve all AuthoritativeEvents targeting an entity_id."""
        sql = (
            "SELECT payload_json FROM authoritative_events "
            "WHERE target_entity_id = ? ORDER BY event_id"
        )
        return self._fetch_many_models(AuthoritativeEvent, sql, target_entity_id)

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
        return self._fetch_many_models(FoodPremises, sql, postal_code)
