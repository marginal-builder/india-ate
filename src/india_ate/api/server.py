"""Stdlib ThreadingHTTPServer wrapper for the india-ate REST API."""

import json
import socketserver
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

from india_ate.api.router import dispatch_request
from india_ate.store import SQLiteStore


class _IndiaAteHTTPServer(ThreadingHTTPServer):
    def __init__(
        self,
        server_address: tuple[str, int],
        request_handler_class: type[BaseHTTPRequestHandler],
        db_path: str,
    ) -> None:
        self.db_path = db_path
        super().__init__(server_address, request_handler_class)

    def server_bind(self) -> None:
        """Bind socket without blocking on reverse DNS via socket.getfqdn."""
        socketserver.TCPServer.server_bind(self)
        host, port = self.server_address[:2]
        self.server_name = str(host) or "localhost"
        self.server_port = int(port)


class _RequestHandler(BaseHTTPRequestHandler):
    def _write_json(self, status: int, payload: dict[str, object]) -> None:
        raw = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def _handle(self, method: str, body: bytes = b"") -> None:
        parsed = urlparse(self.path)
        server = self.server
        if not isinstance(server, _IndiaAteHTTPServer):
            self._write_json(500, {"error": "Invalid server configuration"})
            return
        with SQLiteStore(server.db_path) as store:
            store.initialize()
            status, payload = dispatch_request(
                store, method, parsed.path, parsed.query, body
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
        body = self.rfile.read(length) if length > 0 else b""
        self._handle("POST", body)

    def log_message(self, format: str, *args: object) -> None:
        """Silence default stderr logging in favor of structured telemetry."""
        return


def create_http_server(
    db_path: str, host: str = "127.0.0.1", port: int = 8000
) -> ThreadingHTTPServer:
    """Create a configured ThreadingHTTPServer bound to host:port."""
    return _IndiaAteHTTPServer((host, port), _RequestHandler, db_path)
