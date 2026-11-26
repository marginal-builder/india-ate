"""Unit tests for the public REST API router and HTTP server."""

import http.client
import json
import threading
import urllib.error
import urllib.request
from datetime import UTC, date, datetime
from pathlib import Path

from pydantic import HttpUrl

from india_ate.api.router import dispatch_request
from india_ate.api.server import MAX_REQUEST_BODY_BYTES, create_http_server
from india_ate.models import (
    AuthoritativeEvent,
    BrandListing,
    EvidenceProvenance,
    FoodItem,
    FoodPremises,
    IndiaFSSAI14,
    ScientificStandard,
)
from india_ate.store import SQLiteStore


def _seed(store: SQLiteStore) -> None:
    ts = datetime(2026, 4, 1, 10, 0, tzinfo=UTC)
    prov = EvidenceProvenance(
        source_name="Official Registry",
        source_url=HttpUrl("https://hygiene.fssai.gov.in/snapshot"),
        retrieved_at=ts,
        content_sha256="abc123",
        verification_tier="official_registry",
    )
    premises = FoodPremises(
        entity_id="actor:in:fssai:13624001000999",
        legal_name="Verified Kitchen Ltd",
        jurisdiction_iso="IN",
        regulatory_ids=[IndiaFSSAI14(raw_value="13624001000999")],
        provenance=[prov],
        premises_type="restaurant",
        postal_code="500081",
    )
    store.save_premises(premises)
    store.save_brand_listing(
        BrandListing(
            listing_id="listing:ondc:1",
            display_name="Spice Route",
            platform="ondc",
            premises_entity_id=premises.entity_id,
            postal_code="500081",
            first_seen_at=ts,
            last_seen_at=ts,
            provenance=prov,
        )
    )
    store.save_event(
        AuthoritativeEvent(
            event_id="evt:hygiene:13624001000999:2026-03-01",
            event_type="hygiene_audit",
            target_entity_id=premises.entity_id,
            jurisdiction_iso="IN",
            event_date=date(2026, 3, 1),
            status="5/5",
            verbatim_summary="FSSAI Hygiene Rating 5/5",
            provenance=prov,
        )
    )
    store.save_food_item(
        FoodItem(
            item_id="item:in:ifct:A001",
            canonical_name="Amaranth seed, black",
            item_kind="raw_staple",
            ifct_code="A001",
        )
    )
    store.save_scientific_standard(
        ScientificStandard(
            standard_id="std:in:ifct:A001:protcnt",
            standard_type="nutrient_composition",
            jurisdiction_iso="IN",
            substance_id="sub:ifct:protcnt",
            food_item_id="item:in:ifct:A001",
            value=14.59,
            unit="g/100g",
            provenance=prov,
        )
    )


def test_api_router_endpoints_and_error_paths() -> None:
    with SQLiteStore(":memory:") as store:
        store.initialize()
        _seed(store)

        status, body = dispatch_request(store, "GET", "/health")
        assert status == 200
        assert body["status"] == "ok"

        status, body = dispatch_request(store, "GET", "/v1/decode/10013022000417")
        assert status == 200
        assert body["tier"] == "license"

        status, _ = dispatch_request(store, "GET", "/v1/decode/bad")
        assert status == 400

        status, body = dispatch_request(store, "GET", "/v1/receipt/13624001000999")
        assert status == 200
        assert body["ghost_brand_count"] == 1

        status, body = dispatch_request(store, "GET", "/v1/cluster/13624001000999")
        assert status == 200
        assert len(body["listings"]) == 1  # type: ignore[arg-type]

        status, _ = dispatch_request(store, "GET", "/v1/cluster/10013022000417")
        assert status == 404

        status, body = dispatch_request(store, "GET", "/v1/nearby/500081")
        assert status == 200
        assert len(body["options"]) == 1  # type: ignore[arg-type]

        status, body = dispatch_request(store, "GET", "/v1/foods", query="q=Amaranth")
        assert status == 200
        assert len(body["items"]) == 1  # type: ignore[arg-type]

        status, body = dispatch_request(store, "GET", "/v1/food/item:in:ifct:A001")
        assert status == 200
        assert len(body["standards"]) == 1  # type: ignore[arg-type]

        status, body = dispatch_request(
            store, "GET", "/v1/food/item%3Ain%3Aifct%3AA001"
        )
        assert status == 200
        assert len(body["standards"]) == 1  # type: ignore[arg-type]

        status, _ = dispatch_request(store, "GET", "/v1/food/item:missing")
        assert status == 404

        status, _ = dispatch_request(
            store,
            "POST",
            "/v1/grievance",
            body=json.dumps(
                {
                    "fssai_id": "13624001000999",
                    "issue_category": "spoiled_food",
                    "description": "Food arrived spoiled.",
                    "incident_date": "2026-04-01",
                    "persist": "false",
                }
            ).encode("utf-8"),
        )
        assert status == 400

        status, _ = dispatch_request(store, "POST", "/v1/grievance", body=b"[]")
        assert status == 400

        status, _ = dispatch_request(store, "PUT", "/health")
        assert status == 404

        grievance_payload = json.dumps(
            {
                "fssai_id": "13624001000999",
                "issue_category": "spoiled_food",
                "description": "Food arrived spoiled.",
                "incident_date": "2026-04-01",
            }
        ).encode("utf-8")
        status, body = dispatch_request(
            store, "POST", "/v1/grievance", body=grievance_payload
        )
        assert status == 200
        assert body["escalation_deadline"] == "2026-04-16"
        assert body["ticket_event"] is None

        persist_payload = json.dumps(
            {
                "fssai_id": "13624001000999",
                "issue_category": "spoiled_food",
                "description": "Food arrived spoiled.",
                "incident_date": "2026-04-01",
                "persist": True,
            }
        ).encode("utf-8")
        status, body = dispatch_request(
            store, "POST", "/v1/grievance", body=persist_payload
        )
        assert status == 403
        assert "disabled" in str(body["error"])

        status, body = dispatch_request(
            store,
            "POST",
            "/v1/grievance",
            body=persist_payload,
            allow_grievance_persist=True,
        )
        assert status == 200
        assert body["ticket_event"] is not None

        status, _ = dispatch_request(store, "POST", "/v1/grievance", body=b"{bad")
        assert status == 400

        status, _ = dispatch_request(store, "GET", "/unknown")
        assert status == 404


def test_http_server_roundtrip(tmp_path: Path) -> None:
    db_path = tmp_path / "api.db"
    with SQLiteStore(db_path) as store:
        store.initialize()
        _seed(store)

    server = create_http_server(str(db_path), host="127.0.0.1", port=0)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/health") as resp:
            assert resp.status == 200
            assert resp.headers.get("Content-Type") == "application/json; charset=utf-8"
            assert resp.headers.get("Access-Control-Allow-Origin") == "*"
            assert (
                resp.headers.get("Access-Control-Allow-Methods") == "GET, POST, OPTIONS"
            )
            assert resp.headers.get("Access-Control-Allow-Headers") == "Content-Type"
            assert resp.headers.get("Access-Control-Max-Age") == "600"
            assert resp.headers.get("Cache-Control") == "no-store"
            assert resp.headers.get("X-Content-Type-Options") == "nosniff"
            assert json.loads(resp.read())["status"] == "ok"

        opt_req = urllib.request.Request(
            f"http://127.0.0.1:{port}/v1/grievance", method="OPTIONS"
        )
        with urllib.request.urlopen(opt_req) as resp:
            assert resp.status == 204
            assert resp.headers.get("Access-Control-Allow-Origin") == "*"
            assert (
                resp.headers.get("Access-Control-Allow-Methods") == "GET, POST, OPTIONS"
            )
            assert resp.headers.get("Access-Control-Allow-Headers") == "Content-Type"
            assert resp.headers.get("Access-Control-Max-Age") == "600"
            assert resp.headers.get("Content-Length") == "0"

        try:
            urllib.request.urlopen(f"http://127.0.0.1:{port}/unknown")
            raise AssertionError("Expected HTTPError 404")
        except urllib.error.HTTPError as err:
            assert err.code == 404
            assert err.headers.get("Cache-Control") == "no-store"
            assert err.headers.get("X-Content-Type-Options") == "nosniff"
            assert "error" in json.loads(err.read())

        req = urllib.request.Request(
            f"http://127.0.0.1:{port}/v1/grievance",
            data=json.dumps(
                {
                    "fssai_id": "13624001000999",
                    "issue_category": "misbranded",
                    "description": "Missing FSSAI label.",
                    "incident_date": "2026-04-01",
                }
            ).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req) as resp:
            assert resp.status == 200
            assert json.loads(resp.read())["fssai_id"] == "13624001000999"

        persist_req = urllib.request.Request(
            f"http://127.0.0.1:{port}/v1/grievance",
            data=json.dumps(
                {
                    "fssai_id": "13624001000999",
                    "issue_category": "misbranded",
                    "description": "Missing FSSAI label.",
                    "incident_date": "2026-04-01",
                    "persist": True,
                }
            ).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            urllib.request.urlopen(persist_req)
            raise AssertionError("Expected HTTPError 403")
        except urllib.error.HTTPError as err:
            assert err.code == 403
            assert "disabled" in str(json.loads(err.read())["error"])

        bad_len_req = urllib.request.Request(
            f"http://127.0.0.1:{port}/v1/grievance",
            data=b"{}",
            headers={"Content-Length": "abc"},
            method="POST",
        )
        try:
            urllib.request.urlopen(bad_len_req)
            raise AssertionError("Expected HTTPError 400")
        except urllib.error.HTTPError as err:
            assert err.code == 400

        conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
        try:
            conn.putrequest("POST", "/v1/grievance")
            conn.putheader("Content-Length", str(MAX_REQUEST_BODY_BYTES + 1))
            conn.endheaders()
            response = conn.getresponse()
            assert response.status == 413
            assert "error" in json.loads(response.read())
        finally:
            conn.close()

        negative_conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
        try:
            negative_conn.putrequest("POST", "/v1/grievance")
            negative_conn.putheader("Content-Length", "-1")
            negative_conn.endheaders()
            response = negative_conn.getresponse()
            assert response.status == 400
            assert "error" in json.loads(response.read())
        finally:
            negative_conn.close()

        empty_conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
        try:
            empty_conn.putrequest("POST", "/v1/grievance")
            empty_conn.putheader("Content-Length", "0")
            empty_conn.endheaders()
            response = empty_conn.getresponse()
            assert response.status == 400
            assert "error" in json.loads(response.read())
        finally:
            empty_conn.close()
    finally:
        server.shutdown()
        server.server_close()


def test_http_server_allows_persist_when_explicitly_enabled(tmp_path: Path) -> None:
    db_path = tmp_path / "allowed.db"
    with SQLiteStore(db_path) as store:
        store.initialize()
        _seed(store)

    server = create_http_server(
        str(db_path), host="127.0.0.1", port=0, allow_grievance_persist=True
    )
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        req = urllib.request.Request(
            f"http://127.0.0.1:{port}/v1/grievance",
            data=json.dumps(
                {
                    "fssai_id": "13624001000999",
                    "issue_category": "misbranded",
                    "description": "Missing FSSAI label.",
                    "incident_date": "2026-04-01",
                    "persist": True,
                }
            ).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req) as resp:
            assert resp.status == 200
            assert json.loads(resp.read())["ticket_event"] is not None
    finally:
        server.shutdown()
        server.server_close()
