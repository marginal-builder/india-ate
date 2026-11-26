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

CREATE TABLE IF NOT EXISTS quarantined_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_name TEXT NOT NULL,
    reason TEXT NOT NULL,
    quarantined_at TEXT NOT NULL,
    payload_json TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_quarantined_source
    ON quarantined_records (source_name);
"""

INSERT_PREMISES_SQL = """
INSERT OR REPLACE INTO food_premises (
    entity_id, legal_name, jurisdiction_iso, premises_type,
    address, postal_code, city, state, lat, lon, fssai_id, payload_json
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
"""

INSERT_BRAND_LISTING_SQL = """
INSERT OR REPLACE INTO brand_listings (
    listing_id, display_name, platform, premises_entity_id,
    postal_code, first_seen_at, last_seen_at, payload_json
) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
"""

INSERT_EVENT_SQL = """
INSERT OR REPLACE INTO authoritative_events (
    event_id, event_type, target_entity_id, jurisdiction_iso,
    event_date, status, batch_or_lot_no, verbatim_summary, payload_json
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
"""

INSERT_QUARANTINED_SQL = """
INSERT INTO quarantined_records (
    source_name, reason, quarantined_at, payload_json
) VALUES (?, ?, ?, ?)
"""
