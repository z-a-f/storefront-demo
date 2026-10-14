"""HTTP contracts for the local Storefront app."""

import json
import threading
import unittest
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer

from storefront.server import StorefrontHandler


class StorefrontHTTPTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), StorefrontHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def request(self, method, path, body=None, headers=None):
        connection = HTTPConnection("127.0.0.1", self.server.server_port, timeout=5)
        try:
            connection.request(method, path, body=body, headers=headers or {})
            response = connection.getresponse()
            return response.status, response.getheader("Content-Type"), response.read()
        finally:
            connection.close()

    def test_page_and_assets(self):
        status, content_type, body = self.request("GET", "/")
        self.assertEqual(status, 200)
        self.assertIn("text/html", content_type)
        self.assertIn(b"Agent Controlled Storefront: Best Socks for AI", body)
        for path, mime in (("/app.js", "text/javascript"), ("/styles.css", "text/css")):
            with self.subTest(path=path):
                status, content_type, body = self.request("GET", path)
                self.assertEqual(status, 200)
                self.assertIn(mime, content_type)
                self.assertTrue(body)

    def test_catalog_and_orders(self):
        status, _, body = self.request("GET", "/api/catalog")
        self.assertEqual(status, 200)
        self.assertEqual(len(json.loads(body)), 3)
        status, _, body = self.request("GET", "/api/orders")
        self.assertEqual(status, 200)
        self.assertEqual(len(json.loads(body)), 4)
        self.assertEqual(json.loads(body)[0]["id"], "SF-1001")

    def test_checkout_quote(self):
        status, _, body = self.request(
            "POST",
            "/api/quote",
            json.dumps({"items": [{"sku": "sock-cloud", "quantity": 1}]}),
        )
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)["total_cents"], 2700)

    def test_invalid_and_oversized_requests(self):
        for body in ("not JSON", "[]", '{"items":[]}', '{"items":{},"is_vip":true}'):
            with self.subTest(body=body):
                status, _, payload = self.request("POST", "/api/quote", body)
                self.assertEqual(status, 400)
                self.assertIn("error", json.loads(payload))
        status, _, _ = self.request("POST", "/api/quote", "x" * 8193)
        self.assertEqual(status, 413)

    def test_unknown_paths_and_private_files_are_not_served(self):
        for path in ("/missing", "/../data/orders.json", "/.git/config", "/AGENTS.md"):
            with self.subTest(path=path):
                status, _, _ = self.request("GET", path)
                self.assertEqual(status, 404)
        self.assertEqual(self.request("POST", "/api/orders", "{}")[0], 404)
