"""SQLite DDL schema constants for india-ate."""

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS food_premises (
    entity_id TEXT PRIMARY KEY,
    legal_name TEXT NOT NULL,
    jurisdiction_iso TEXT NOT NULL,
    premises_type TEXT NOT NULL,
    address TEXT,
    postal_code TEXT,
    city TEXT,
    state TEXT,
    lat REAL,
    lon REAL,
    fssai_id TEXT,
    payload_json TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_premises_fssai ON food_premises (fssai_id);
CREATE INDEX IF NOT EXISTS idx_premises_postal ON food_premises (postal_code);

CREATE TABLE IF NOT EXISTS brand_listings (
    listing_id TEXT PRIMARY KEY,
    display_name TEXT NOT NULL,
    platform TEXT NOT NULL,
    premises_entity_id TEXT NOT NULL,
    postal_code TEXT,
    first_seen_at TEXT NOT NULL,
    last_seen_at TEXT NOT NULL,
    payload_json TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_listings_premises
    ON brand_listings (premises_entity_id);

CREATE TABLE IF NOT EXISTS authoritative_events (
    event_id TEXT PRIMARY KEY,
    event_type TEXT NOT NULL,
    target_entity_id TEXT NOT NULL,
    jurisdiction_iso TEXT NOT NULL,
    event_date TEXT NOT NULL,
    status TEXT NOT NULL,
    batch_or_lot_no TEXT,
    verbatim_summary TEXT NOT NULL,
    payload_json TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_events_target
    ON authoritative_events (target_entity_id);
"""
