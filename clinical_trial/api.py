"""Local HTTP adapter for validated synthetic-case review reports.

This standard-library server is intentionally for local development and CI. It
does not provide authentication, TLS, rate limiting, or production hardening.
"""

import argparse
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import sys
import sqlite3

from .investigator import investigate
from .reviews import ConflictError, ReviewStore
from .agent import run_agent

from .registry import (
    MAX_REGISTRY_BYTES, TrustedRegistry, registry_from_json,
    report_from_registry_json,
)
from .report import CaseValidationError, MAX_INPUT_BYTES, _unique_object, _reject_constant


def _json_bytes(value: dict) -> bytes:
    return json.dumps(value, ensure_ascii=True, allow_nan=False,
                      separators=(",", ":")).encode("utf-8")


class ApiHandler(BaseHTTPRequestHandler):
    """Bounded API surface that never logs request contents."""

    protocol_version = "HTTP/1.1"
    server_version = "TrialInvestigator"
    sys_version = ""
    source_registry: TrustedRegistry | None = None
    review_store: ReviewStore | None = None
    planner_factory = None

    def setup(self):
        super().setup()
        self.connection.settimeout(10)

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
        self.send_header("Connection", "close")
        self.close_connection = True
        if allow:
            self.send_header("Allow", allow)
        self.end_headers()
        self.wfile.write(body)

    def _error(self, status: HTTPStatus, code: str):
        self._send(status, {"error": code})

    def do_GET(self):  # noqa: N802 - BaseHTTPRequestHandler API
        assets = {"/": ("workspace.html", "text/html"),
                  "/workspace.js": ("workspace.js", "text/javascript"),
                  "/workspace.css": ("workspace.css", "text/css")}
        if self.path in assets:
            filename, content_type = assets[self.path]
            body = (Path(__file__).resolve().parents[1] / "web" / filename).read_bytes()
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", content_type + "; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Content-Security-Policy", "default-src 'self'; frame-ancestors 'none'; object-src 'none'")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)
            return
        if self.path == "/v1/demo":
            request = json.loads((Path(__file__).resolve().parents[1] / "examples/synthetic_request.json").read_text())
            request.pop("schema_version")
            request.pop("findings")
            self._send(HTTPStatus.OK, request)
            return
        if self.path.startswith("/v1/reports/") and self.path != "/v1/reports/validate":
            try:
                self._send(HTTPStatus.OK, self.review_store.get(self.path.removeprefix("/v1/reports/")))
            except (KeyError, AttributeError):
                self._error(HTTPStatus.NOT_FOUND, "not_found")
            return
        if self.path == "/health":
            self._send(HTTPStatus.OK, {"status": "ok"})
            return
        if self.path == "/v1/reports/validate":
            self._send(HTTPStatus.METHOD_NOT_ALLOWED, {"error": "method_not_allowed"},
                       allow="POST")
            return
        self._error(HTTPStatus.NOT_FOUND, "not_found")

    def do_POST(self):  # noqa: N802 - BaseHTTPRequestHandler API
        if self.path not in ("/v1/reports/validate", "/v1/investigate", "/v1/reviews"):
            self._error(HTTPStatus.NOT_FOUND, "not_found")
            return
        if self.headers.get("Transfer-Encoding") or len(self.headers.get_all("Content-Length", [])) > 1:
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
            if self.path == "/v1/reports/validate":
                report = report_from_registry_json(payload, self.source_registry)
            else:
                if self.review_store is None:
                    self._error(HTTPStatus.SERVICE_UNAVAILABLE, "review_storage_unavailable")
                    return
                request = json.loads(payload.decode("utf-8"), object_pairs_hook=_unique_object,
                                     parse_constant=_reject_constant)
                if type(request) is not dict:
                    raise ValueError("object required")
                if self.path == "/v1/investigate":
                    if self.planner_factory is None:
                        result = investigate(self.source_registry, request)
                    else:
                        planner = self.planner_factory()
                        result = run_agent(self.source_registry, request, planner)
                        result['execution'] = {'engine':'azure-bounded-agent', 'tool_calls':len(result['agent_trace']),
                                               'usage':planner.usage, 'model_cost_usd':None}
                    report = self.review_store.create(result)
                else:
                    if set(request) != {"identifier", "revision", "criterion_id", "verdict", "reason", "reviewer"}:
                        raise ValueError("invalid correction fields")
                    report = self.review_store.correct(**request)
        except ConflictError:
            self._error(HTTPStatus.CONFLICT, "revision_conflict")
            return
        except sqlite3.Error:
            self._error(HTTPStatus.SERVICE_UNAVAILABLE, "storage_unavailable")
            return
        except (ValueError, TypeError, KeyError, RecursionError):
            self._error(HTTPStatus.BAD_REQUEST, "invalid_case")
            return
        self._send(HTTPStatus.OK, report)


def handler_for(registry: TrustedRegistry, store: ReviewStore | None = None, planner=None) -> type[ApiHandler]:
    """Bind one immutable registry to a server without global mutation."""
    if not isinstance(registry, TrustedRegistry):
        raise ValueError("validated registry required")

    class RegistryApiHandler(ApiHandler):
        source_registry = registry
        review_store = store
        planner_factory = staticmethod(planner) if planner else None

    return RegistryApiHandler


def serve(registry: TrustedRegistry, host: str = "127.0.0.1",
          port: int = 8000, store: ReviewStore | None = None, planner=None) -> None:
    """Serve local requests until interrupted."""
    with ThreadingHTTPServer((host, port), handler_for(registry, store, planner)) as server:
        server.serve_forever()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("registry", type=Path,
                        help="operator-controlled synthetic source registry JSON")
    parser.add_argument('--azure-model', action='store_true', help='Enable paid model calls using configured environment variables')
    args = parser.parse_args()
    try:
        with args.registry.open("rb") as stream:
            registry = registry_from_json(stream.read(MAX_REGISTRY_BYTES + 1))
        data_directory = Path("local-data")
        data_directory.mkdir(exist_ok=True)
        planner = None
        if args.azure_model:
            from .azure_planner import AzurePlanner
            AzurePlanner.from_environment()  # Validate once before binding.
            planner = AzurePlanner.from_environment
        serve(registry, store=ReviewStore(data_directory / "reviews.db"), planner=planner)
    except KeyboardInterrupt:
        pass
    except (OSError, CaseValidationError, ValueError):
        print("API not started: trusted source registry is invalid.", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
