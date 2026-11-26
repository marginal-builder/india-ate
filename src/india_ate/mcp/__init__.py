"""MCP (Model Context Protocol) JSON-RPC 2.0 server for india-ate."""

from india_ate.mcp.server import handle_jsonrpc_request, serve_mcp_stdio

__all__ = ["handle_jsonrpc_request", "serve_mcp_stdio"]
