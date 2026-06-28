"""Localhost-only HTTP debug harness for compiled query contracts.

The real runtime auth model is per-request caller identity. This module binds one
identity at server startup to exercise the local fixture path without building an
auth subsystem. It is NOT an auth server — do not expose beyond localhost.
"""

from __future__ import annotations

import ipaddress
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from clearmetric.core import load_artifact_file
from clearmetric.core.errors import (
    ClearMetricError,
    PolicyDeniedError,
    QueryExecutionError,
)
from clearmetric.policy import require_gated_identity

from . import execute_project_query


def validate_loopback_host(host: str) -> str:
    """Refuse non-loopback bind addresses."""
    normalized = host.strip().lower()
    if normalized in {"localhost", "127.0.0.1", "::1"}:
        return host.strip()
    try:
        address = ipaddress.ip_address(normalized)
    except ValueError as exc:
        raise ClearMetricError(
            f"serve host must be loopback-only (got {host!r}); "
            "this is a single-identity local debug harness, not an auth server"
        ) from exc
    if not address.is_loopback:
        raise ClearMetricError(
            f"serve refuses non-loopback host {host!r}; "
            "bind to 127.0.0.1 or localhost only"
        )
    return host.strip()


def serve_project(
    *,
    artifact_path: Path,
    project_dir: Path,
    identity: str,
    rules_path: Path,
    host: str = "127.0.0.1",
    port: int = 8765,
) -> None:
    """Run a minimal localhost HTTP server for gated query execution."""
    host = validate_loopback_host(host)
    identity = require_gated_identity(identity)
    artifact = load_artifact_file(artifact_path.expanduser().resolve())
    project_root = project_dir.expanduser().resolve()
    rules = rules_path.expanduser().resolve()

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, format: str, *args: Any) -> None:
            return

        def _send_json(self, status: int, payload: dict[str, Any]) -> None:
            body = json.dumps(payload).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self) -> None:
            if urlparse(self.path).path == "/health":
                self._send_json(
                    200,
                    {
                        "status": "ok",
                        "identity": identity,
                        "note": "single-identity local debug harness; not an auth server",
                    },
                )
                return
            self._send_json(404, {"error": "not found"})

        def do_POST(self) -> None:
            if urlparse(self.path).path != "/query":
                self._send_json(404, {"error": "not found"})
                return
            length_header = self.headers.get("Content-Length", "0")
            try:
                length = int(length_header)
            except ValueError:
                self._send_json(400, {"error": "invalid Content-Length header"})
                return
            if length < 0:
                self._send_json(400, {"error": "invalid Content-Length header"})
                return
            raw = self.rfile.read(length).decode("utf-8") if length else "{}"
            try:
                body = json.loads(raw)
            except json.JSONDecodeError:
                self._send_json(400, {"error": "invalid JSON body"})
                return
            query_id = body.get("query_id")
            if not query_id or not isinstance(query_id, str):
                self._send_json(400, {"error": "query_id required"})
                return
            try:
                rows = execute_project_query(
                    artifact,
                    identity=identity,
                    rules_path=rules,
                    query_selection=query_id,
                    project_dir=project_root,
                )
            except PolicyDeniedError as exc:
                self._send_json(403, {"error": str(exc)})
                return
            except (ClearMetricError, QueryExecutionError) as exc:
                self._send_json(500, {"error": str(exc)})
                return
            self._send_json(200, {"rows": rows})

    server = HTTPServer((host, port), Handler)
    print(
        f"cm serve: http://{host}:{port} "
        f"(identity={identity!r}; local debug harness only)",
        flush=True,
    )
    server.serve_forever()


__all__ = ["serve_project", "validate_loopback_host"]
