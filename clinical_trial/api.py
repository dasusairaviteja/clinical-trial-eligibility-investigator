"""Local HTTP adapter for validated synthetic-case review reports.

This standard-library server is intentionally for local development and CI. It
does not provide authentication, TLS, rate limiting, or production hardening.
"""

from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json

from .report import CaseValidationError, MAX_INPUT_BYTES, report_from_json


def _json_bytes(value: dict) -> bytes:
    return json.dumps(value, ensure_ascii=True, allow_nan=False,
                      separators=(",", ":")).encode("utf-8")


class ApiHandler(BaseHTTPRequestHandler):
    """Bounded API surface that never logs request contents."""

    protocol_version = "HTTP/1.1"
    server_version = "TrialInvestigator"
    sys_version = ""

    def log_message(self, format, *args):  # noqa: A002 - stdlib callback name
        """Avoid the default request log; case identifiers can be sensitive."""

    def _send(self, status: HTTPStatus, value: dict, *, allow: str | None = None):
        body = _json_bytes(value)
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'none'; frame-ancestors 'none'")
        self.send_header("Referrer-Policy", "no-referrer")
        if allow:
            self.send_header("Allow", allow)
        self.end_headers()
        self.wfile.write(body)

    def _error(self, status: HTTPStatus, code: str):
        self._send(status, {"error": code})

    def do_GET(self):  # noqa: N802 - BaseHTTPRequestHandler API
        if self.path == "/health":
            self._send(HTTPStatus.OK, {"status": "ok"})
            return
        if self.path == "/v1/reports/validate":
            self._send(HTTPStatus.METHOD_NOT_ALLOWED, {"error": "method_not_allowed"},
                       allow="POST")
            return
        self._error(HTTPStatus.NOT_FOUND, "not_found")

    def do_POST(self):  # noqa: N802 - BaseHTTPRequestHandler API
        if self.path != "/v1/reports/validate":
            self._error(HTTPStatus.NOT_FOUND, "not_found")
            return
        if self.headers.get("Transfer-Encoding"):
            self._error(HTTPStatus.BAD_REQUEST, "unsupported_transfer_encoding")
            return
        content_type = self.headers.get_content_type()
        if content_type != "application/json":
            self._error(HTTPStatus.UNSUPPORTED_MEDIA_TYPE, "application_json_required")
            return
        raw_length = self.headers.get("Content-Length")
        try:
            length = int(raw_length) if raw_length is not None else -1
        except ValueError:
            length = -1
        if length < 0:
            self._error(HTTPStatus.LENGTH_REQUIRED, "valid_content_length_required")
            return
        if length > MAX_INPUT_BYTES:
            self._error(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, "case_too_large")
            return
        payload = self.rfile.read(length)
        if len(payload) != length:
            self._error(HTTPStatus.BAD_REQUEST, "incomplete_request_body")
            return
        try:
            report = report_from_json(payload)
        except CaseValidationError:
            self._error(HTTPStatus.BAD_REQUEST, "invalid_case")
            return
        self._send(HTTPStatus.OK, report)


def serve(host: str = "127.0.0.1", port: int = 8000) -> None:
    """Serve local requests until interrupted."""
    with ThreadingHTTPServer((host, port), ApiHandler) as server:
        server.serve_forever()


def main() -> int:
    try:
        serve()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
