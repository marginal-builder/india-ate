"""Parameterized SQLite runtime persistence store for india-ate."""

import sqlite3
from pathlib import Path
from typing import Self

from pydantic import BaseModel, ConfigDict

from india_ate.models import AuthoritativeEvent, BrandListing, FoodPremises
from india_ate.store._schema import SCHEMA_SQL

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

    def save_premises(self, premises: FoodPremises) -> None:
        """Insert or replace a FoodPremises record."""
        sql = """
        INSERT OR REPLACE INTO food_premises (
            entity_id, legal_name, jurisdiction_iso, premises_type,
            address, postal_code, city, state, lat, lon, fssai_id, payload_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
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
        self._conn.execute(sql, params)
        self._conn.commit()

    def get_premises_by_entity_id(self, entity_id: str) -> FoodPremises | None:
        """Retrieve a FoodPremises by its canonical entity_id."""
        cur = self._conn.execute(
            "SELECT payload_json FROM food_premises WHERE entity_id = ?",
            (entity_id,),
        )
        row = cur.fetchone()
        return FoodPremises.model_validate_json(row[0]) if row is not None else None

    def get_premises_by_fssai_id(self, fssai_id: str) -> FoodPremises | None:
        """Retrieve a FoodPremises by its 14-digit FSSAI ID."""
        cur = self._conn.execute(
            "SELECT payload_json FROM food_premises WHERE fssai_id = ?",
            (fssai_id,),
        )
        row = cur.fetchone()
        return FoodPremises.model_validate_json(row[0]) if row is not None else None

    def save_brand_listing(self, listing: BrandListing) -> None:
        """Insert or replace a BrandListing record."""
        sql = """
        INSERT OR REPLACE INTO brand_listings (
            listing_id, display_name, platform, premises_entity_id,
            postal_code, first_seen_at, last_seen_at, payload_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
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
        self._conn.execute(sql, params)
        self._conn.commit()

    def get_brand_listings_for_premises(
        self, premises_entity_id: str
    ) -> list[BrandListing]:
        """Retrieve all BrandListings linked to a premises_entity_id."""
        cur = self._conn.execute(
            "SELECT payload_json FROM brand_listings "
            "WHERE premises_entity_id = ? ORDER BY listing_id",
            (premises_entity_id,),
        )
        return [BrandListing.model_validate_json(r[0]) for r in cur.fetchall()]

    def save_event(self, event: AuthoritativeEvent) -> None:
        """Insert or replace an AuthoritativeEvent record."""
        sql = """
        INSERT OR REPLACE INTO authoritative_events (
            event_id, event_type, target_entity_id, jurisdiction_iso,
            event_date, status, batch_or_lot_no, verbatim_summary, payload_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
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
        self._conn.execute(sql, params)
        self._conn.commit()

    def get_events_for_target(self, target_entity_id: str) -> list[AuthoritativeEvent]:
        """Retrieve all AuthoritativeEvents targeting an entity_id."""
        cur = self._conn.execute(
            "SELECT payload_json FROM authoritative_events "
            "WHERE target_entity_id = ? ORDER BY event_id",
            (target_entity_id,),
        )
        return [AuthoritativeEvent.model_validate_json(r[0]) for r in cur.fetchall()]

    def query_ghost_brand_cluster(self, fssai_id: str) -> GhostBrandCluster | None:
        """Query the physical premises and all brand listings for an FSSAI ID."""
        premises = self.get_premises_by_fssai_id(fssai_id)
        if premises is None:
            return None
        listings = self.get_brand_listings_for_premises(premises.entity_id)
        return GhostBrandCluster(premises=premises, listings=listings)

    def query_nearby_premises(self, postal_code: str) -> list[FoodPremises]:
        """Query all FoodPremises in a given postal_code."""
        cur = self._conn.execute(
            "SELECT payload_json FROM food_premises "
            "WHERE postal_code = ? ORDER BY entity_id",
            (postal_code,),
        )
        return [FoodPremises.model_validate_json(r[0]) for r in cur.fetchall()]
