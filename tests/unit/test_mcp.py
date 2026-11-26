"""Unit tests for the JSON-RPC 2.0 MCP server."""

import io
import json
from datetime import UTC, date, datetime

from pydantic import HttpUrl

from india_ate.mcp.server import handle_jsonrpc_request, serve_mcp_stdio
from india_ate.models import (
    AuthoritativeEvent,
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


def test_mcp_initialize_tools_list_and_calls() -> None:
    with SQLiteStore(":memory:") as store:
        store.initialize()
        _seed(store)

        init_resp = handle_jsonrpc_request(
            store, {"jsonrpc": "2.0", "id": 1, "method": "initialize"}
        )
        assert init_resp is not None
        assert init_resp["result"]["serverInfo"]["name"] == "india-ate"

        assert (
            handle_jsonrpc_request(
                store, {"jsonrpc": "2.0", "method": "notifications/initialized"}
            )
            is None
        )

        list_resp = handle_jsonrpc_request(
            store, {"jsonrpc": "2.0", "id": 2, "method": "tools/list"}
        )
        assert list_resp is not None
        tools = list_resp["result"]["tools"]
        assert len(tools) == 6

        decode_resp = handle_jsonrpc_request(
            store,
            {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "decode_fssai",
                    "arguments": {"fssai_id": "10013022000417"},
                },
            },
        )
        assert decode_resp is not None
        decoded = json.loads(decode_resp["result"]["content"][0]["text"])
        assert decoded["tier"] == "license"

        receipt_resp = handle_jsonrpc_request(
            store,
            {
                "jsonrpc": "2.0",
                "id": 4,
                "method": "tools/call",
                "params": {
                    "name": "get_fact_receipt",
                    "arguments": {"fssai_id": "13624001000999"},
                },
            },
        )
        assert receipt_resp is not None
        receipt = json.loads(receipt_resp["result"]["content"][0]["text"])
        assert receipt["premises"]["legal_name"] == "Verified Kitchen Ltd"

        nearby_resp = handle_jsonrpc_request(
            store,
            {
                "jsonrpc": "2.0",
                "id": 5,
                "method": "tools/call",
                "params": {
                    "name": "find_verified_nearby_switches",
                    "arguments": {"postal_code": "500081"},
                },
            },
        )
        assert nearby_resp is not None
        nearby = json.loads(nearby_resp["result"]["content"][0]["text"])
        assert len(nearby["options"]) == 1

        food_resp = handle_jsonrpc_request(
            store,
            {
                "jsonrpc": "2.0",
                "id": 6,
                "method": "tools/call",
                "params": {
                    "name": "lookup_food_nutrition",
                    "arguments": {"query": "Amaranth"},
                },
            },
        )
        assert food_resp is not None
        foods = json.loads(food_resp["result"]["content"][0]["text"])
        assert len(foods["results"]) == 1

        unknown_tool = handle_jsonrpc_request(
            store,
            {
                "jsonrpc": "2.0",
                "id": 7,
                "method": "tools/call",
                "params": {"name": "nonexistent", "arguments": {}},
            },
        )
        assert unknown_tool is not None
        assert "error" in unknown_tool

        cluster_resp = handle_jsonrpc_request(
            store,
            {
                "jsonrpc": "2.0",
                "id": 8,
                "method": "tools/call",
                "params": {
                    "name": "get_ghost_brand_cluster",
                    "arguments": {"fssai_id": "13624001000999"},
                },
            },
        )
        assert cluster_resp is not None
        assert "premises" in json.loads(cluster_resp["result"]["content"][0]["text"])

        grievance_resp = handle_jsonrpc_request(
            store,
            {
                "jsonrpc": "2.0",
                "id": 9,
                "method": "tools/call",
                "params": {
                    "name": "generate_grievance_packet",
                    "arguments": {
                        "fssai_id": "13624001000999",
                        "issue_category": "spoiled_food",
                        "description": "Spoiled delivery",
                        "incident_date": "2026-04-01",
                    },
                },
            },
        )
        assert grievance_resp is not None
        grievance = json.loads(grievance_resp["result"]["content"][0]["text"])
        assert grievance["escalation_deadline"] == "2026-04-16"


def test_mcp_error_paths_and_stdio_loop() -> None:
    with SQLiteStore(":memory:") as store:
        store.initialize()
        bad_params = handle_jsonrpc_request(
            store,
            {
                "jsonrpc": "2.0",
                "id": 10,
                "method": "tools/call",
                "params": ["bad"],
            },
        )
        assert bad_params is not None
        assert bad_params["error"]["code"] == -32602

        bad_args = handle_jsonrpc_request(
            store,
            {
                "jsonrpc": "2.0",
                "id": 11,
                "method": "tools/call",
                "params": {"name": "decode_fssai", "arguments": ["bad"]},
            },
        )
        assert bad_args is not None
        assert bad_args["error"]["code"] == -32602

        missing_arg = handle_jsonrpc_request(
            store,
            {
                "jsonrpc": "2.0",
                "id": 12,
                "method": "tools/call",
                "params": {"name": "decode_fssai", "arguments": {}},
            },
        )
        assert missing_arg is not None
        assert missing_arg["error"]["code"] == -32602

        unknown_method = handle_jsonrpc_request(
            store, {"jsonrpc": "2.0", "id": 13, "method": "unknown/method"}
        )
        assert unknown_method is not None
        assert unknown_method["error"]["code"] == -32601

    stdin = io.StringIO(
        "\n"
        + json.dumps({"jsonrpc": "2.0", "id": 1, "method": "ping"})
        + "\n"
        + "{bad json\n"
        + "[]\n"
    )
    stdout = io.StringIO()
    serve_mcp_stdio(":memory:", stdin=stdin, stdout=stdout)
    lines = [json.loads(line) for line in stdout.getvalue().strip().splitlines()]
    assert len(lines) == 3
    assert lines[0]["result"] == {}
    assert lines[1]["error"]["code"] == -32700
    assert lines[2]["error"]["code"] == -32600
