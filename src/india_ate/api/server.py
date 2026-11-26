"""Stdlib ThreadingHTTPServer wrapper for the india-ate REST API."""

import json
import socketserver
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

from india_ate.api.router import dispatch_request
from india_ate.store import SQLiteStore

MAX_REQUEST_BODY_BYTES = 1_000_000


class _IndiaAteHTTPServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(
        self,
        server_address: tuple[str, int],
        request_handler_class: type[BaseHTTPRequestHandler],
        db_path: str,
        allow_grievance_persist: bool = False,
    ) -> None:
        self.db_path = db_path
        self.allow_grievance_persist = allow_grievance_persist
        super().__init__(server_address, request_handler_class)

    def server_bind(self) -> None:
        """Bind socket without blocking on reverse DNS via socket.getfqdn."""
        socketserver.TCPServer.server_bind(self)
        host, port = self.server_address[:2]
        self.server_name = str(host) or "localhost"
        self.server_port = int(port)


class _RequestHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def _send_cors_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Max-Age", "600")

    def _write_json(self, status: int, payload: dict[str, object]) -> None:
        raw = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self._send_cors_headers()
        self.end_headers()
        self.wfile.write(raw)

    def do_OPTIONS(self) -> None:  # noqa: N802
        """Handle CORS preflight requests."""
        self.send_response(204)
        self._send_cors_headers()
        self.send_header("Content-Length", "0")
        self.end_headers()

    def _handle(self, method: str, body: bytes = b"") -> None:
        parsed = urlparse(self.path)
        server = self.server
        if not isinstance(server, _IndiaAteHTTPServer):
            self._write_json(500, {"error": "Invalid server configuration"})
            return
        with SQLiteStore(server.db_path) as store:
            store.initialize()
            status, payload = dispatch_request(
                store,
                method,
                parsed.path,
                parsed.query,
                body,
                allow_grievance_persist=server.allow_grievance_persist,
            )
        self._write_json(status, payload)

    def do_GET(self) -> None:  # noqa: N802
        """Handle HTTP GET requests."""
        self._handle("GET")

    def do_POST(self) -> None:  # noqa: N802
        """Handle HTTP POST requests."""
        raw_len = self.headers.get("Content-Length", "0")
        try:
            length = int(raw_len)
        except ValueError:
            self._write_json(400, {"error": "Invalid Content-Length"})
            return
        if length < 0:
            self._write_json(400, {"error": "Negative Content-Length"})
            return
        if length > MAX_REQUEST_BODY_BYTES:
            self.close_connection = True
            self._write_json(413, {"error": "Request body too large"})
            return
        body = self.rfile.read(length) if length > 0 else b""
        self._handle("POST", body)

    def log_message(self, format: str, *args: object) -> None:
        """Silence default stderr logging; deployments add their own access logs."""
        return


def create_http_server(
    db_path: str,
    host: str = "127.0.0.1",
    port: int = 8000,
    *,
    allow_grievance_persist: bool = False,
) -> ThreadingHTTPServer:
    """Create a configured ThreadingHTTPServer bound to host:port."""
    return _IndiaAteHTTPServer(
        (host, port),
        _RequestHandler,
        db_path,
        allow_grievance_persist=allow_grievance_persist,
    )
