# ruff: noqa: INP001 - standalone prototype under a hyphenated artifact directory
"""Serve the project cockpit and proxy one read-only Cargento endpoint."""

from __future__ import annotations

import argparse
import http.server
import json
import urllib.error
import urllib.request
from pathlib import Path
from typing import ClassVar

ROOT = Path(__file__).resolve().parent
MAX_PAYLOAD_BYTES = 4 << 20


def read_live_payload(source_port: int) -> bytes:
    """Read one bounded snapshot without using environment proxy settings."""
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    request = urllib.request.Request(
        f"http://127.0.0.1:{source_port}/api/data",
        headers={"Host": f"127.0.0.1:{source_port}"},
    )
    with opener.open(request, timeout=5) as response:
        payload = response.read(MAX_PAYLOAD_BYTES + 1)
    if len(payload) > MAX_PAYLOAD_BYTES:
        raise ValueError("live Cargento payload exceeds the prototype limit")
    value = json.loads(payload)
    if not isinstance(value, dict):
        raise TypeError("live Cargento payload is not an object")
    return json.dumps(value, separators=(",", ":"), ensure_ascii=False).encode()


class CockpitHandler(http.server.SimpleHTTPRequestHandler):
    """Serve static prototype assets plus a same-origin read-only proxy."""

    source_port: ClassVar[int] = 4553

    def __init__(self, *args: object, **kwargs: object) -> None:
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; connect-src 'self'; style-src 'self'; script-src 'self'",
        )
        self.send_header("X-Content-Type-Options", "nosniff")
        super().end_headers()

    def do_GET(self) -> None:
        if self.path == "/live-data":
            self._send_live_data()
            return
        if self.path == "/health":
            self._send_json(200, {"ok": True, "source_port": self.source_port})
            return
        super().do_GET()

    def _send_live_data(self) -> None:
        try:
            payload = read_live_payload(self.source_port)
        except (OSError, TypeError, ValueError, urllib.error.URLError) as exc:
            self._send_json(
                502,
                {
                    "error": "live Cargento snapshot unavailable",
                    "failure": type(exc).__name__,
                },
            )
            return
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _send_json(self, status: int, value: dict[str, object]) -> None:
        payload = json.dumps(value, separators=(",", ":")).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--source-port", type=int, default=4553)
    args = parser.parse_args()
    CockpitHandler.source_port = args.source_port
    server = http.server.ThreadingHTTPServer(("127.0.0.1", args.port), CockpitHandler)
    print(f"Project cockpit: http://127.0.0.1:{args.port}", flush=True)
    print(f"Live Cargento source: http://127.0.0.1:{args.source_port}/api/data", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
