"""Public REST API router and HTTP server for india-ate."""

from india_ate.api.router import dispatch_request
from india_ate.api.server import create_http_server

__all__ = ["create_http_server", "dispatch_request"]
