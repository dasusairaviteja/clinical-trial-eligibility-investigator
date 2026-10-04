import http.client
import json
from pathlib import Path
import threading
import unittest

from clinical_trial.api import ApiHandler
from clinical_trial.report import MAX_INPUT_BYTES
from http.server import ThreadingHTTPServer

EXAMPLE = Path(__file__).resolve().parents[1] / "examples" / "synthetic_case.json"


class ApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), ApiHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.host, cls.port = cls.server.server_address

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)

    def request(self, method, path, body=None, headers=None):
        connection = http.client.HTTPConnection(self.host, self.port, timeout=2)
        connection.request(method, path, body=body, headers=headers or {})
        response = connection.getresponse()
        payload = response.read()
        result = response.status, dict(response.getheaders()), json.loads(payload)
        connection.close()
        return result

    def test_health_is_minimal_and_not_cached(self):
        status, headers, body = self.request("GET", "/health")
        self.assertEqual((status, body), (200, {"status": "ok"}))
        self.assertEqual(headers["Cache-Control"], "no-store")
        self.assertEqual(headers["X-Content-Type-Options"], "nosniff")
        self.assertEqual(headers["Referrer-Policy"], "no-referrer")

    def test_valid_case_returns_review_report(self):
        status, _, body = self.request(
            "POST", "/v1/reports/validate", EXAMPLE.read_bytes(),
            {"Content-Type": "application/json"})
        self.assertEqual(status, 200)
        self.assertEqual(body["status"], "human_review_required")
        self.assertNotIn("sources", body)

    def test_invalid_case_is_rejected_without_input_echo(self):
        marker = b'{"private":"PRIVATE_INPUT_MARKER"}'
        status, _, body = self.request("POST", "/v1/reports/validate", marker,
                                       {"Content-Type": "application/json"})
        self.assertEqual((status, body), (400, {"error": "invalid_case"}))
        self.assertNotIn("PRIVATE_INPUT_MARKER", json.dumps(body))

    def test_wrong_media_type_is_rejected(self):
        status, _, body = self.request("POST", "/v1/reports/validate", b"{}",
                                       {"Content-Type": "text/plain"})
        self.assertEqual((status, body),
                         (415, {"error": "application_json_required"}))

    def test_oversize_body_is_rejected_before_read(self):
        status, _, body = self.request("POST", "/v1/reports/validate", None, {
            "Content-Type": "application/json", "Content-Length": str(MAX_INPUT_BYTES + 1)
        })
        self.assertEqual((status, body), (413, {"error": "case_too_large"}))

    def test_transfer_encoding_is_rejected(self):
        status, _, body = self.request("POST", "/v1/reports/validate", b"0\r\n\r\n", {
            "Content-Type": "application/json", "Transfer-Encoding": "chunked"
        })
        self.assertEqual((status, body),
                         (400, {"error": "unsupported_transfer_encoding"}))

    def test_unknown_route_and_wrong_method_are_distinct(self):
        status, _, body = self.request("GET", "/missing")
        self.assertEqual((status, body), (404, {"error": "not_found"}))
        status, headers, body = self.request("GET", "/v1/reports/validate")
        self.assertEqual((status, body), (405, {"error": "method_not_allowed"}))
        self.assertEqual(headers["Allow"], "POST")


if __name__ == "__main__":
    unittest.main()
