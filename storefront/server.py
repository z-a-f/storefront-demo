"""Local Storefront server with catalog, orders, and checkout quote APIs."""

import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from storefront.orders import catalog, quote, sample_orders

STATIC_DIR = Path(__file__).resolve().parent / "static"
ASSETS = {
    "/": ("index.html", "text/html"),
    "/styles.css": ("styles.css", "text/css"),
    "/app.js": ("app.js", "text/javascript"),
}


class StorefrontHandler(BaseHTTPRequestHandler):
    def _send(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type + "; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _json(self, status: int, value: object) -> None:
        self._send(status, json.dumps(value).encode(), "application/json")

    def do_GET(self) -> None:
        path = urlsplit(self.path).path
        if path in ASSETS:
            name, content_type = ASSETS[path]
            self._send(200, (STATIC_DIR / name).read_bytes(), content_type)
        elif path == "/api/catalog":
            self._json(200, catalog())
        elif path == "/api/orders":
            self._json(200, sample_orders())
        else:
            self._json(404, {"error": "Page not found"})

    def do_POST(self) -> None:
        if urlsplit(self.path).path != "/api/quote":
            self._json(404, {"error": "Endpoint not found"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 8192:
                self._json(413, {"error": "Request must contain 1 to 8192 bytes"})
                return
            payload = json.loads(self.rfile.read(length))
            if not isinstance(payload, dict):
                raise ValueError("Checkout request must be an object")
            result = quote(payload.get("items"), is_vip=payload.get("is_vip", False))
        except (ValueError, UnicodeDecodeError) as error:
            self._json(400, {"error": str(error)})
            return
        self._json(200, result)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    with ThreadingHTTPServer(("127.0.0.1", args.port), StorefrontHandler) as server:
        print(f"Storefront: http://127.0.0.1:{server.server_port}", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
