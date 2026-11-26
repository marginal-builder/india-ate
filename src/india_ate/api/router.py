"""Framework-independent REST API router over india-ate services."""

import json
from datetime import date
from typing import cast
from urllib.parse import parse_qs, unquote

from india_ate.models import IndiaFSSAI14
from india_ate.services import (
    GrievanceCategory,
    build_fact_receipt,
    find_verified_nearby_switches,
    generate_grievance_packet,
    get_ghost_brand_cluster,
)
from india_ate.store import SQLiteStore


def _parse_grievance_payload(body: bytes) -> dict[str, object]:
    payload = json.loads(body.decode("utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Request body must be a JSON object")
    persist_raw = payload.get("persist", False)
    if not isinstance(persist_raw, bool):
        raise ValueError("persist must be a boolean")
    return payload


def _handle_grievance_post(
    store: SQLiteStore, body: bytes
) -> tuple[int, dict[str, object]]:
    try:
        payload = _parse_grievance_payload(body)
        order_ref = payload.get("order_reference")
        packet = generate_grievance_packet(
            store=store,
            fssai_id=str(payload["fssai_id"]),
            issue_category=cast(GrievanceCategory, str(payload["issue_category"])),
            order_reference=str(order_ref) if order_ref is not None else None,
            description=str(payload["description"]),
            incident_date=date.fromisoformat(str(payload["incident_date"])),
            persist=bool(payload.get("persist", False)),
        )
    except (ValueError, KeyError, TypeError) as exc:
        return 400, {"error": str(exc)}
    return 200, packet.model_dump(mode="json")


def _handle_get_fssai_route(
    store: SQLiteStore, prefix: str, fssai_id: str
) -> tuple[int, dict[str, object]]:
    try:
        if prefix == "decode":
            return 200, IndiaFSSAI14(raw_value=fssai_id).decode_offline()
        if prefix == "receipt":
            return 200, build_fact_receipt(store, fssai_id).model_dump(mode="json")
        cluster = get_ghost_brand_cluster(store, fssai_id)
        if cluster is None:
            return 404, {"error": "Premises not found"}
        return 200, cluster.model_dump(mode="json")
    except ValueError as exc:
        return 400, {"error": str(exc)}


def _handle_get_foods(
    store: SQLiteStore, path: str, query: str
) -> tuple[int, dict[str, object]]:
    if path == "/v1/foods":
        params = parse_qs(query)
        q = params.get("q", [""])[0]
        items = [item.model_dump(mode="json") for item in store.search_food_items(q)]
        return 200, {"items": items}
    item_id = unquote(path.removeprefix("/v1/food/"))
    item = store.get_food_item(item_id)
    if item is None:
        return 404, {"error": "Food item not found"}
    standards = [
        std.model_dump(mode="json")
        for std in store.get_standards_for_food_item(item.item_id)
    ]
    return 200, {"item": item.model_dump(mode="json"), "standards": standards}


def _dispatch_get(
    store: SQLiteStore, path: str, query: str
) -> tuple[int, dict[str, object]]:
    if path == "/health":
        return 200, {"status": "ok"}
    for prefix in ("decode", "receipt", "cluster"):
        if path.startswith(f"/v1/{prefix}/"):
            return _handle_get_fssai_route(
                store, prefix, unquote(path.split("/", 3)[3])
            )
    if path.startswith("/v1/nearby/"):
        pin = unquote(path.removeprefix("/v1/nearby/"))
        options = [
            opt.model_dump(mode="json")
            for opt in find_verified_nearby_switches(store, pin)
        ]
        return 200, {"postal_code": pin, "options": options}
    if path == "/v1/foods" or path.startswith("/v1/food/"):
        return _handle_get_foods(store, path, query)
    return 404, {"error": "Not found"}


def dispatch_request(
    store: SQLiteStore,
    method: str,
    path: str,
    query: str = "",
    body: bytes = b"",
) -> tuple[int, dict[str, object]]:
    """Dispatch an HTTP request to the appropriate service and return (status, json)."""
    if method == "POST" and path == "/v1/grievance":
        return _handle_grievance_post(store, body)
    if method == "GET":
        return _dispatch_get(store, path, query)
    return 404, {"error": "Not found"}
