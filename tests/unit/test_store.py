"""Unit tests for SQLite, JSONL, and DuckDB/Parquet stores."""

from datetime import UTC, date, datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from india_ate.models import (
    AuthoritativeEvent,
    BrandListing,
    EvidenceProvenance,
    FoodItem,
    FoodPremises,
    IndiaFSSAI14,
    IngestionBatch,
    RegulatoryIdentifier,
    ScientificStandard,
    Substance,
)
from india_ate.store import (
    SQLiteStore,
    export_jsonl,
    export_parquet_snapshots,
    import_jsonl,
    query_enforcement_summary,
    query_ghost_brand_clusters_by_postal_code,
    write_parquet_table,
)


def test_sqlite_store_crud_cluster_nearby_and_sqli_safety(
    tmp_path: Path,
    official_provenance: EvidenceProvenance,
) -> None:
    db_path = tmp_path / "india_ate.db"
    premises_a = FoodPremises(
        entity_id="actor:in:fssai:23624001000123",
        legal_name="Deccan Cloud Hospitality",
        jurisdiction_iso="IN",
        regulatory_ids=[IndiaFSSAI14(raw_value="23624001000123")],
        provenance=[official_provenance],
        premises_type="cloud_kitchen",
        postal_code="500081",
        city="Hyderabad",
        state="Telangana",
    )
    premises_b = FoodPremises(
        entity_id="actor:in:fssai:13624001000999",
        legal_name="Hyderabad Kitchen B",
        jurisdiction_iso="IN",
        regulatory_ids=[IndiaFSSAI14(raw_value="13624001000999")],
        provenance=[official_provenance],
        premises_type="restaurant",
        postal_code="500081",
    )
    premises_c = FoodPremises(
        entity_id="actor:in:fssai:10013022000417",
        legal_name="Acme Foods Pvt Ltd",
        jurisdiction_iso="IN",
        regulatory_ids=[IndiaFSSAI14(raw_value="10013022000417")],
        provenance=[official_provenance],
        premises_type="co_packer_factory",
        postal_code="400001",
    )
    ts = datetime(2026, 4, 1, 9, 0, tzinfo=UTC)
    listings = [
        BrandListing(
            listing_id=f"listing:swiggy:{idx}",
            display_name=name,
            platform="swiggy",
            premises_entity_id=premises_a.entity_id,
            postal_code="500081",
            first_seen_at=ts,
            last_seen_at=ts,
            provenance=official_provenance,
        )
        for idx, name in enumerate(
            ["Royal Biryani Kitchen", "Midnight Bowl Co", "Nawab Express"], start=1
        )
    ]
    event = AuthoritativeEvent(
        event_id="evt:tgsafe:raid:2026-42",
        event_type="enforcement_raid_or_suspension",
        target_entity_id=premises_a.entity_id,
        jurisdiction_iso="IN",
        event_date=date(2026, 4, 2),
        status="Suspended",
        verbatim_summary="License suspended.",
        provenance=official_provenance,
    )

    with SQLiteStore(db_path) as store:
        store.initialize()
        for p in (premises_a, premises_b, premises_c):
            store.save_premises(p)
        for listing in listings:
            store.save_brand_listing(listing)
        store.save_event(event)

        assert store.get_premises_by_entity_id(premises_c.entity_id) == premises_c
        assert store.get_premises_by_fssai_id("10013022000417") == premises_c
        assert store.get_premises_by_entity_id("missing") is None
        assert len(store.get_brand_listings_for_premises(premises_a.entity_id)) == 3
        assert len(store.get_events_for_target(premises_a.entity_id)) == 1

        cluster = store.query_ghost_brand_cluster("23624001000123")
        assert cluster is not None
        assert cluster.premises == premises_a
        assert len(cluster.listings) == 3

        nearby = store.query_nearby_premises("500081")
        assert {p.entity_id for p in nearby} == {
            premises_a.entity_id,
            premises_b.entity_id,
        }

        sqli = "' OR '1'='1'; DROP TABLE food_premises; --"
        assert store.query_ghost_brand_cluster(sqli) is None
        assert store.query_nearby_premises(sqli) == []
        assert store.get_premises_by_entity_id(premises_c.entity_id) == premises_c

        no_fssai = FoodPremises(
            entity_id="actor:us:fda:3001",
            legal_name="US Facility",
            jurisdiction_iso="US",
            provenance=[official_provenance],
            premises_type="warehouse",
        )
        store.save_premises(no_fssai)
        assert store.get_premises_by_entity_id(no_fssai.entity_id) == no_fssai


def test_sqlite_store_default_in_memory_and_nested_parent_creation(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    sample_premises: FoodPremises,
) -> None:
    empty_cwd = tmp_path / "cwd"
    empty_cwd.mkdir()
    monkeypatch.chdir(empty_cwd)

    with SQLiteStore() as mem_store:
        mem_store.initialize()
        mem_store.save_premises(sample_premises)
        assert (
            mem_store.get_premises_by_entity_id(sample_premises.entity_id)
            == sample_premises
        )
    assert list(empty_cwd.iterdir()) == []

    nested_db = tmp_path / "nested" / "sub" / "india_ate.db"
    with SQLiteStore(nested_db) as disk_store:
        disk_store.initialize()
        disk_store.save_premises(sample_premises)
    with SQLiteStore(nested_db) as reopened:
        assert (
            reopened.get_premises_by_entity_id(sample_premises.entity_id)
            == sample_premises
        )


def test_jsonl_roundtrip_empty_and_malformed(
    tmp_path: Path,
    sample_premises: FoodPremises,
    sample_brand_listing: BrandListing,
    sample_food_item: FoodItem,
    sample_substance: Substance,
    sample_standard: ScientificStandard,
    sample_event: AuthoritativeEvent,
) -> None:
    unicode_premises = sample_premises.model_copy(
        update={"legal_name": "Masala Café — दिल्ली"}
    )
    entities = [
        unicode_premises,
        sample_brand_listing,
        sample_food_item,
        sample_substance,
        sample_standard,
        sample_event,
    ]
    out_file = tmp_path / "nested" / "sub" / "entities.jsonl"
    assert export_jsonl(entities, out_file) == len(entities)
    raw_text = out_file.read_text(encoding="utf-8")
    assert raw_text.endswith("\n")
    assert "Masala Café — दिल्ली" in raw_text
    assert "\\u" not in raw_text
    lines = raw_text.splitlines()
    assert len(lines) == len(entities)
    reconstructed = import_jsonl(out_file)
    assert reconstructed == entities

    empty_file = tmp_path / "empty.jsonl"
    assert export_jsonl([], empty_file) == 0
    assert empty_file.read_text(encoding="utf-8") == ""
    assert import_jsonl(empty_file) == []

    bad_json = tmp_path / "bad.jsonl"
    bad_json.write_text("{truncated\n", encoding="utf-8")
    with pytest.raises(ValueError):
        import_jsonl(bad_json)

    bad_envelope = tmp_path / "bad_envelope.jsonl"
    bad_envelope.write_text(
        '{"entity_type": "UnknownModel", "payload": {}}\n', encoding="utf-8"
    )
    with pytest.raises(
        ValueError, match=r"^Unknown or missing entity_type: 'UnknownModel'$"
    ):
        import_jsonl(bad_envelope)

    bad_payload = tmp_path / "bad_payload.jsonl"
    bad_payload.write_text(
        '{"entity_type": "FoodItem", "payload": {"item_id": "x"}}\n', encoding="utf-8"
    )
    with pytest.raises(ValidationError):
        import_jsonl(bad_payload)

    non_dict = tmp_path / "non_dict.jsonl"
    non_dict.write_text("[1, 2, 3]\n", encoding="utf-8")
    with pytest.raises(ValueError, match=r"^JSONL line must decode to a JSON object$"):
        import_jsonl(non_dict)

    missing_payload = tmp_path / "missing_payload.jsonl"
    missing_payload.write_text('{"entity_type": "FoodItem"}\n', encoding="utf-8")
    with pytest.raises(ValueError, match=r"^JSONL record missing 'payload' field$"):
        import_jsonl(missing_payload)


def test_duckdb_parquet_export_and_analytics(
    tmp_path: Path,
    official_provenance: EvidenceProvenance,
) -> None:
    db_path = tmp_path / "india_ate.db"
    snap_dir = tmp_path / "nested" / "snapshots"
    p1 = FoodPremises(
        entity_id="actor:in:fssai:23624001000123",
        legal_name="Deccan Cloud",
        jurisdiction_iso="IN",
        regulatory_ids=[IndiaFSSAI14(raw_value="23624001000123")],
        provenance=[official_provenance],
        premises_type="cloud_kitchen",
        postal_code="500081",
    )
    p2 = FoodPremises(
        entity_id="actor:in:fssai:10013022000417",
        legal_name="Mumbai Bakery",
        jurisdiction_iso="IN",
        regulatory_ids=[IndiaFSSAI14(raw_value="10013022000417")],
        provenance=[official_provenance],
        premises_type="restaurant",
        postal_code="400001",
    )
    ts = datetime(2026, 4, 1, 9, 0, tzinfo=UTC)
    listings = [
        BrandListing(
            listing_id="listing:swiggy:101",
            display_name="Royal Biryani Kitchen",
            platform="swiggy",
            premises_entity_id=p1.entity_id,
            postal_code="500081",
            first_seen_at=ts,
            last_seen_at=ts,
            provenance=official_provenance,
        ),
        BrandListing(
            listing_id="listing:zomato:202",
            display_name="Midnight Bowl Co",
            platform="zomato",
            premises_entity_id=p1.entity_id,
            postal_code="500081",
            first_seen_at=ts,
            last_seen_at=ts,
            provenance=official_provenance,
        ),
        BrandListing(
            listing_id="listing:swiggy:303",
            display_name="Nawab Express",
            platform="swiggy",
            premises_entity_id=p1.entity_id,
            postal_code="500081",
            first_seen_at=ts,
            last_seen_at=ts,
            provenance=official_provenance,
        ),
        BrandListing(
            listing_id="listing:ondc:404",
            display_name="Mumbai Bakery",
            platform="ondc",
            premises_entity_id=p2.entity_id,
            postal_code="400001",
            first_seen_at=ts,
            last_seen_at=ts,
            provenance=official_provenance,
        ),
    ]
    events = [
        AuthoritativeEvent(
            event_id="evt:raid:1",
            event_type="enforcement_raid_or_suspension",
            target_entity_id=p1.entity_id,
            jurisdiction_iso="IN",
            event_date=date(2026, 4, 1),
            status="Suspended",
            verbatim_summary="Suspended 1.",
            provenance=official_provenance,
        ),
        AuthoritativeEvent(
            event_id="evt:raid:2",
            event_type="enforcement_raid_or_suspension",
            target_entity_id=p1.entity_id,
            jurisdiction_iso="IN",
            event_date=date(2026, 4, 2),
            status="Suspended",
            verbatim_summary="Suspended 2.",
            provenance=official_provenance,
        ),
        AuthoritativeEvent(
            event_id="evt:audit:1",
            event_type="hygiene_audit",
            target_entity_id=p2.entity_id,
            jurisdiction_iso="IN",
            event_date=date(2026, 4, 3),
            status="Active",
            verbatim_summary="Hygiene rating 4/5.",
            provenance=official_provenance,
        ),
    ]

    with SQLiteStore(db_path) as store:
        store.initialize()
        store.save_premises(p1)
        store.save_premises(p2)
        for listing in listings:
            store.save_brand_listing(listing)
        for event in events:
            store.save_event(event)

    outputs = export_parquet_snapshots(db_path, snap_dir)
    # Re-export into already existing directory to verify exist_ok=True.
    outputs = export_parquet_snapshots(db_path, snap_dir)
    assert set(outputs.keys()) == {
        "food_premises",
        "brand_listings",
        "authoritative_events",
    }
    for pq_path in outputs.values():
        assert pq_path.exists()
        assert pq_path.stat().st_size > 0

    clusters = {
        row["postal_code"]: row
        for row in query_ghost_brand_clusters_by_postal_code(snap_dir)
    }
    assert clusters["500081"]["premises_count"] == 1
    assert clusters["500081"]["brand_listing_count"] == 3
    assert clusters["400001"]["premises_count"] == 1
    assert clusters["400001"]["brand_listing_count"] == 1

    summary = {
        (row["event_type"], row["status"]): row["count"]
        for row in query_enforcement_summary(snap_dir)
    }
    assert summary[("enforcement_raid_or_suspension", "Suspended")] == 2
    assert summary[("hygiene_audit", "Active")] == 1

    empty_pq = write_parquet_table(
        [],
        [("entity_id", "VARCHAR")],
        tmp_path / "nested_pq" / "sub" / "empty.parquet",
    )
    assert empty_pq.exists()

    with pytest.raises(ValueError, match=r"^Invalid column definition:"):
        write_parquet_table([], [("bad col", "VARCHAR")], snap_dir / "bad.parquet")
    with pytest.raises(ValueError, match=r"^Invalid column definition:"):
        write_parquet_table([], [("valid_col", "INT")], snap_dir / "bad_type.parquet")


def test_sqlite_store_save_premises_merges_provenance_reg_ids_and_optional_fields(
    official_provenance: EvidenceProvenance,
) -> None:
    from pydantic import HttpUrl

    second_provenance = EvidenceProvenance(
        source_name="ONDC Retail Catalog",
        source_url=HttpUrl("https://ondc.org/catalog/snapshot.json"),
        retrieved_at=datetime(2026, 4, 2, 12, 0, tzinfo=UTC),
        content_sha256="cafebabe",
        verification_tier="user_verified_snapshot",
    )
    fssai_reg = IndiaFSSAI14(raw_value="23624001000123")
    gstin_reg = RegulatoryIdentifier(
        jurisdiction_iso="IN",
        scheme="IN_GSTIN",
        raw_value="36AABCU9603R1ZM",
    )

    first = FoodPremises(
        entity_id="actor:in:fssai:23624001000123",
        legal_name="Deccan Cloud Hospitality",
        jurisdiction_iso="IN",
        regulatory_ids=[fssai_reg],
        provenance=[official_provenance],
        premises_type="cloud_kitchen",
        address="Plot 12, Jubilee Hills",
        postal_code="500033",
        city="Hyderabad",
        state="Telangana",
        lat=17.4326,
        lon=78.4071,
    )
    second_with_nulls = FoodPremises(
        entity_id="actor:in:fssai:23624001000123",
        legal_name="Deccan Cloud Hospitality",
        jurisdiction_iso="IN",
        regulatory_ids=[fssai_reg, gstin_reg],
        provenance=[official_provenance, second_provenance],
        premises_type="cloud_kitchen",
        address=None,
        postal_code=None,
        city=None,
        state=None,
        lat=None,
        lon=None,
    )

    with SQLiteStore(":memory:") as store:
        store.initialize()
        store.save_premises(first)
        store.save_premises(second_with_nulls)

        merged = store.get_premises_by_entity_id(first.entity_id)
        assert merged is not None
        assert merged.provenance == [official_provenance, second_provenance]
        assert merged.regulatory_ids == [fssai_reg, gstin_reg]
        assert merged.address == "Plot 12, Jubilee Hills"
        assert merged.postal_code == "500033"
        assert merged.city == "Hyderabad"
        assert merged.state == "Telangana"
        assert merged.lat == 17.4326
        assert merged.lon == 78.4071
        assert [p.entity_id for p in store.query_nearby_premises("500033")] == [
            first.entity_id
        ]

        # Incoming non-null values (including 0.0) override existing values,
        # and subsequent None preserves 0.0.
        zero_coords = FoodPremises(
            entity_id="actor:in:fssai:23624001000123",
            legal_name="Deccan Cloud Hospitality",
            jurisdiction_iso="IN",
            regulatory_ids=[fssai_reg],
            provenance=[second_provenance],
            premises_type="cloud_kitchen",
            address="Updated Address",
            lat=0.0,
            lon=0.0,
        )
        store.save_premises(zero_coords)
        updated = store.get_premises_by_entity_id(first.entity_id)
        assert updated is not None
        assert updated.address == "Updated Address"
        assert updated.lat == 0.0
        assert updated.lon == 0.0
        assert updated.postal_code == "500033"

        store.save_premises(second_with_nulls)
        preserved_zero = store.get_premises_by_entity_id(first.entity_id)
        assert preserved_zero is not None
        assert preserved_zero.lat == 0.0
        assert preserved_zero.lon == 0.0


def test_sqlite_store_save_ingestion_batch_merges_premises_across_adapters(
    official_provenance: EvidenceProvenance,
) -> None:
    from pydantic import HttpUrl

    recall_prov = EvidenceProvenance(
        source_name="FSSAI FoSCoS Recall",
        source_url=HttpUrl("https://foscos.fssai.gov.in/recalls"),
        retrieved_at=datetime(2026, 4, 3, 8, 0, tzinfo=UTC),
        content_sha256="12345678",
        verification_tier="official_registry",
    )
    fssai_reg = IndiaFSSAI14(raw_value="10013022000417")
    p_adapter1 = FoodPremises(
        entity_id="actor:in:fssai:10013022000417",
        legal_name="Acme Foods Pvt Ltd",
        jurisdiction_iso="IN",
        regulatory_ids=[fssai_reg],
        provenance=[official_provenance],
        premises_type="co_packer_factory",
        postal_code="400001",
        city="Mumbai",
    )
    p_adapter2 = FoodPremises(
        entity_id="actor:in:fssai:10013022000417",
        legal_name="Acme Foods Pvt Ltd",
        jurisdiction_iso="IN",
        regulatory_ids=[fssai_reg],
        provenance=[recall_prov],
        premises_type="co_packer_factory",
        postal_code=None,
        city=None,
        state="Maharashtra",
    )

    with SQLiteStore(":memory:") as store:
        store.initialize()
        store.save_ingestion_batch(
            IngestionBatch(entities=[p_adapter1], quarantined=[])
        )
        store.save_ingestion_batch(
            IngestionBatch(entities=[p_adapter2], quarantined=[])
        )

        loaded = store.get_premises_by_entity_id(p_adapter1.entity_id)
        assert loaded is not None
        assert loaded.provenance == [official_provenance, recall_prov]
        assert loaded.regulatory_ids == [fssai_reg]
        assert loaded.postal_code == "400001"
        assert loaded.city == "Mumbai"
        assert loaded.state == "Maharashtra"
