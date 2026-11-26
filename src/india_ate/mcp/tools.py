"""MCP tool definitions and execution handlers over india-ate services."""

from datetime import date
from typing import Any, cast

from india_ate.models import IndiaFSSAI14
from india_ate.services import (
    GrievanceCategory,
    build_fact_receipt,
    find_verified_nearby_switches,
    generate_grievance_packet,
    get_ghost_brand_cluster,
)
from india_ate.store import SQLiteStore

MCP_TOOLS: list[dict[str, object]] = [
    {
        "name": "decode_fssai",
        "description": "Deterministically decode a 14-digit FSSAI ID offline.",
        "inputSchema": {
            "type": "object",
            "properties": {"fssai_id": {"type": "string"}},
            "required": ["fssai_id"],
        },
    },
    {
        "name": "get_fact_receipt",
        "description": "Return an objective Fact Receipt for a 14-digit FSSAI ID.",
        "inputSchema": {
            "type": "object",
            "properties": {"fssai_id": {"type": "string"}},
            "required": ["fssai_id"],
        },
    },
    {
        "name": "get_ghost_brand_cluster",
        "description": "List all platform BrandListings sharing a 14-digit FSSAI ID.",
        "inputSchema": {
            "type": "object",
            "properties": {"fssai_id": {"type": "string"}},
            "required": ["fssai_id"],
        },
    },
    {
        "name": "find_verified_nearby_switches",
        "description": "Find audited or Tier-1 licensed premises in a pin code.",
        "inputSchema": {
            "type": "object",
            "properties": {"postal_code": {"type": "string"}},
            "required": ["postal_code"],
        },
    },
    {
        "name": "lookup_food_nutrition",
        "description": "Search IFCT FoodItems and linked ScientificStandards.",
        "inputSchema": {
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        },
    },
    {
        "name": "generate_grievance_packet",
        "description": "Generate a Food Safety Connect grievance packet.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "fssai_id": {"type": "string"},
                "issue_category": {"type": "string"},
                "description": {"type": "string"},
                "incident_date": {"type": "string"},
                "order_reference": {"type": "string"},
            },
            "required": ["fssai_id", "issue_category", "description", "incident_date"],
        },
    },
]


def _tool_lookup_food(store: SQLiteStore, args: dict[str, Any]) -> dict[str, object]:
    query = str(args["query"])
    items = store.search_food_items(query)
    results = [
        {
            "item": item.model_dump(mode="json"),
            "standards": [
                s.model_dump(mode="json")
                for s in store.get_standards_for_food_item(item.item_id)
            ],
        }
        for item in items
    ]
    return {"query": query, "results": results}


def _tool_grievance(store: SQLiteStore, args: dict[str, Any]) -> dict[str, object]:
    packet = generate_grievance_packet(
        store=store,
        fssai_id=str(args["fssai_id"]),
        issue_category=cast(GrievanceCategory, str(args["issue_category"])),
        order_reference=(
            str(args["order_reference"])
            if args.get("order_reference") is not None
            else None
        ),
        description=str(args["description"]),
        incident_date=date.fromisoformat(str(args["incident_date"])),
    )
    return packet.model_dump(mode="json")


def _tool_nearby(store: SQLiteStore, args: dict[str, Any]) -> dict[str, object]:
    pin = str(args["postal_code"])
    options = [
        opt.model_dump(mode="json") for opt in find_verified_nearby_switches(store, pin)
    ]
    return {"postal_code": pin, "options": options}


def _tool_cluster(store: SQLiteStore, args: dict[str, Any]) -> dict[str, object]:
    cluster = get_ghost_brand_cluster(store, str(args["fssai_id"]))
    return cluster.model_dump(mode="json") if cluster else {"premises": None}


class UnknownToolError(Exception):
    """Raised when an MCP client invokes an unregistered tool name."""


def call_mcp_tool(
    store: SQLiteStore, name: str, args: dict[str, Any]
) -> dict[str, object]:
    """Execute a named MCP tool against SQLiteStore and return JSON dict."""
    if name == "decode_fssai":
        return IndiaFSSAI14(raw_value=str(args["fssai_id"])).decode_offline()
    if name == "get_fact_receipt":
        return build_fact_receipt(store, str(args["fssai_id"])).model_dump(mode="json")
    if name == "get_ghost_brand_cluster":
        return _tool_cluster(store, args)
    if name == "find_verified_nearby_switches":
        return _tool_nearby(store, args)
    if name == "lookup_food_nutrition":
        return _tool_lookup_food(store, args)
    if name == "generate_grievance_packet":
        return _tool_grievance(store, args)
    raise UnknownToolError(f"Unknown MCP tool: {name}")
