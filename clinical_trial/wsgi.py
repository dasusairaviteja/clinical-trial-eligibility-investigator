"""Authenticated WSGI research service; run behind a TLS buffering proxy.

One worker is intentional: request limits are process-local and SQLite is local.
Tokens are individual reviewer credentials, supplied by a secret store at startup.
"""

import hashlib
import hmac
import json
import logging
import os
from pathlib import Path
import sqlite3
import threading
import time
import uuid

from .agent import run_agent
from .investigator import investigate
from .registry import registry_from_json, report_from_registry_json, MAX_REGISTRY_BYTES
from .report import MAX_INPUT_BYTES, _unique_object, _reject_constant
from .reviews import ReviewStore, ConflictError

ROOT = Path(__file__).resolve().parents[1]
LOG = logging.getLogger("trial.requests")


class Application:
    def __init__(self, registry, store, credentials, planner=None, rate_limit=60):
        if not isinstance(credentials, dict) or not credentials or any(not isinstance(token, str) or not isinstance(identity, str) or len(token) < 32 or not identity.strip()
                                  for token, identity in credentials.items()):
            raise ValueError("individual tokens must contain at least 32 characters")
        if type(rate_limit) is not int or rate_limit < 1:
            raise ValueError("positive rate limit required")
        self.credentials = [(hashlib.sha256(k.encode()).digest(), v)
                            for k, v in credentials.items()]
        self.registry, self.store, self.planner = registry, store, planner
        self.rate_limit = rate_limit
        self.windows = {}
        self.lock = threading.Lock()
        self.active = threading.BoundedSemaphore(2)

    def authenticate(self, environ):
        header = environ.get("HTTP_AUTHORIZATION", "")
        if not header.startswith("Bearer "):
            return None
        digest = hashlib.sha256(header[7:].encode()).digest()
        return next((identity for token, identity in self.credentials
                     if hmac.compare_digest(token, digest)), None)

    def __call__(self, environ, start_response):
        started, request_id = time.monotonic(), uuid.uuid4().hex
        status, content_type = 200, "application/json; charset=utf-8"
        try:
            status, value, content_type = self.dispatch(environ)
            body = value if isinstance(value, bytes) else json.dumps(value, allow_nan=False).encode()
        except ConflictError:
            status, body = 409, b'{"error":"revision_conflict"}'
        except KeyError:
            status, body = 404, b'{"error":"not_found"}'
        except (ValueError, TypeError, RecursionError):
            status, body = 400, b'{"error":"invalid_request"}'
        except sqlite3.Error:
            status, body = 503, b'{"error":"storage_unavailable"}'
        except Exception:
            # Never include request data, exception messages, or credentials in logs.
            status, body = 500, b'{"error":"internal_error"}'
        from http import HTTPStatus
        headers = [("Content-Type", content_type), ("Content-Length", str(len(body))),
                   ("Cache-Control", "no-store"), ("X-Content-Type-Options", "nosniff"),
                   ("Referrer-Policy", "no-referrer"), ("X-Request-ID", request_id),
                   ("Content-Security-Policy", "default-src 'self'; frame-ancestors 'none'; object-src 'none'; base-uri 'none'; form-action 'self'")]
        if status == 401:
            headers.append(("WWW-Authenticate", "Bearer"))
        if status in (429, 503):
            headers.append(("Retry-After", "60"))
        start_response(f"{status} {HTTPStatus(status).phrase}", headers)
        LOG.info(json.dumps({"request_id": request_id, "status": status,
                             "duration_ms": round((time.monotonic()-started)*1000, 2)}))
        return [body]

    def dispatch(self, env):
        path, method = env.get("PATH_INFO", ""), env.get("REQUEST_METHOD", "GET")
        mime = "application/json; charset=utf-8"
        if path == "/health" and method == "GET":
            return 200, {"status": "ok"}, mime
        assets = {"/": ("workspace.html", "text/html"),
                  "/workspace.css": ("workspace.css", "text/css"),
                  "/workspace.js": ("workspace.js", "text/javascript")}
        if path in assets and method == "GET":
            filename, kind = assets[path]
            return 200, (ROOT / "web" / filename).read_bytes(), kind + "; charset=utf-8"
        identity = self.authenticate(env)
        if identity is None:
            return 401, {"error": "authentication_required"}, mime
        # Bounded by the configured credential set, not untrusted IP strings.
        with self.lock:
            minute = int(time.monotonic() // 60)
            window, count = self.windows.get(identity, (minute, 0))
            count = count + 1 if window == minute else 1
            self.windows[identity] = (minute, count)
            if count > self.rate_limit:
                return 429, {"error": "rate_limit"}, mime
        if method == "GET":
            if path == "/v1/me":
                return 200, {"reviewer": identity}, mime
            if path == "/v1/demo":
                value = json.loads((ROOT / "examples/synthetic_request.json").read_text())
                return 200, {k: v for k, v in value.items() if k not in ("schema_version", "findings")}, mime
            if path.startswith("/v1/reports/"):
                return 200, self.store.get(path.removeprefix("/v1/reports/")), mime
            return 404, {"error": "not_found"}, mime
        if method != "POST":
            return 405, {"error": "method_not_allowed"}, mime
        if path not in ("/v1/investigate", "/v1/reviews", "/v1/reports/validate"):
            return 404, {"error": "not_found"}, mime
        if env.get("CONTENT_TYPE", "").split(";")[0].strip() != "application/json":
            return 415, {"error": "application_json_required"}, mime
        if env.get("HTTP_TRANSFER_ENCODING"):
            return 400, {"error": "unsupported_transfer_encoding"}, mime
        length = int(env.get("CONTENT_LENGTH") or -1)
        if length < 0:
            return 411, {"error": "content_length_required"}, mime
        if length > MAX_INPUT_BYTES:
            return 413, {"error": "request_too_large"}, mime
        payload = env["wsgi.input"].read(length)
        if len(payload) != length:
            raise ValueError("short body")
        request = json.loads(payload, object_pairs_hook=_unique_object, parse_constant=_reject_constant)
        if type(request) is not dict:
            raise ValueError("object required")
        if path == "/v1/reports/validate":
            return 200, report_from_registry_json(payload, self.registry), mime
        if path == "/v1/reviews":
            if set(request) != {"identifier", "revision", "criterion_id", "verdict", "reason", "reviewer"}:
                raise ValueError("invalid correction")
            request["reviewer"] = identity  # Never trust a caller's claimed identity.
            return 200, self.store.correct(**request), mime
        if not self.active.acquire(blocking=False):
            return 503, {"error": "investigation_capacity"}, mime
        try:
            if self.planner:
                planner = self.planner()
                result = run_agent(self.registry, request, planner)
                result["execution"] = {"engine": "bounded-agent", "tool_calls": len(result["agent_trace"]),
                                       "usage": planner.usage, "model_cost_usd": None}
            else:
                result = investigate(self.registry, request)
            return 200, self.store.create(result), mime
        finally:
            self.active.release()


def create_app():
    """Fail closed on missing auth; .env files are never implicitly loaded."""
    if not LOG.handlers:
        LOG.addHandler(logging.StreamHandler())
    LOG.setLevel(logging.INFO)
    LOG.propagate = False
    credentials = json.loads(os.environ["REVIEWER_TOKENS_JSON"])
    if type(credentials) is not dict:
        raise ValueError("credential mapping required")
    registry_path = Path(os.environ.get("REGISTRY_PATH", "examples/synthetic_sources.json"))
    with registry_path.open("rb") as stream:
        registry = registry_from_json(stream.read(MAX_REGISTRY_BYTES + 1))
    database = Path(os.environ.get("REVIEW_DATABASE", "local-data/reviews.db"))
    database.parent.mkdir(parents=True, exist_ok=True)
    planner = None
    if os.environ.get("ENABLE_AZURE_MODEL") == "true":
        from .azure_planner import AzurePlanner
        AzurePlanner.from_environment()
        planner = AzurePlanner.from_environment
    return Application(registry, ReviewStore(database), credentials, planner)
