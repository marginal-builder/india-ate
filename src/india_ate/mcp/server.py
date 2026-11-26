"""JSON-RPC 2.0 stdio transport for the india-ate MCP server."""

import json
import sys
from typing import Any, TextIO

from india_ate.mcp.tools import MCP_TOOLS, UnknownToolError, call_mcp_tool
from india_ate.store import SQLiteStore

PROTOCOL_VERSION = "2024-11-05"


def _error_response(req_id: object, code: int, message: str) -> dict[str, Any]:
    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "error": {"code": code, "message": message},
    }


def _handle_tools_call(
    store: SQLiteStore, req_id: object, params: object
) -> dict[str, Any]:
    if not isinstance(params, dict):
        return _error_response(req_id, -32602, "Tool params must be an object")
    name = str(params.get("name", ""))
    args = params.get("arguments")
    if args is None:
        args = {}
    if not isinstance(args, dict):
        return _error_response(req_id, -32602, "Tool arguments must be an object")
    try:
        result = call_mcp_tool(store, name, args)
    except UnknownToolError as exc:
        return _error_response(req_id, -32601, str(exc))
    except (KeyError, ValueError, TypeError) as exc:
        return _error_response(req_id, -32602, str(exc))
    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "result": {"content": [{"type": "text", "text": json.dumps(result)}]},
    }


def _initialize_result(req_id: object) -> dict[str, Any]:
    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "result": {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "india-ate", "version": "0.1.0"},
        },
    }


def handle_jsonrpc_request(
    store: SQLiteStore, payload: object
) -> dict[str, Any] | None:
    """Dispatch a single JSON-RPC 2.0 MCP request."""
    if not isinstance(payload, dict):
        return _error_response(None, -32600, "Invalid Request")
    method = payload.get("method")
    req_id = payload.get("id")
    if method == "notifications/initialized":
        return None
    if method == "initialize":
        return _initialize_result(req_id)
    if method == "ping":
        return {"jsonrpc": "2.0", "id": req_id, "result": {}}
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": req_id, "result": {"tools": MCP_TOOLS}}
    if method == "tools/call":
        return _handle_tools_call(store, req_id, payload.get("params"))
    return _error_response(req_id, -32601, f"Method not found: {method}")


def _process_stdio_line(store: SQLiteStore, line: str) -> dict[str, Any] | None:
    try:
        payload = json.loads(line)
    except json.JSONDecodeError:
        return _error_response(None, -32700, "Parse error")
    return handle_jsonrpc_request(store, payload)


def serve_mcp_stdio(
    db_path: str,
    stdin: TextIO | None = None,
    stdout: TextIO | None = None,
) -> None:
    """Run line-delimited JSON-RPC 2.0 MCP server loop over stdio."""
    in_stream = stdin or sys.stdin
    out_stream = stdout or sys.stdout
    with SQLiteStore(db_path) as store:
        store.initialize()
        for line in in_stream:
            stripped = line.strip()
            if not stripped:
                continue
            resp = _process_stdio_line(store, stripped)
            if resp is not None:
                out_stream.write(json.dumps(resp) + "\n")
                out_stream.flush()
