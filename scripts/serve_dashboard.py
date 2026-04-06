#!/usr/bin/env python3
"""Serve web/ over HTTP so ashby_dashboard.html can fetch glasses_data.json (external mode)."""

from __future__ import annotations

import argparse
import webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "web"


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB), **kwargs)

    def log_message(self, format: str, *args) -> None:
        print("[%s] %s - %s" % (self.log_date_time_string(), args[0], format % args[1:]))


def main() -> None:
    p = argparse.ArgumentParser(description="HTTP server for Glass Ashby dashboard")
    p.add_argument("--port", type=int, default=8765)
    p.add_argument("--no-browser", action="store_true")
    args = p.parse_args()

    if not WEB.is_dir():
        raise SystemExit(f"Missing folder: {WEB}")

    url = f"http://127.0.0.1:{args.port}/ashby_dashboard.html"
    httpd = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    print(f"Serving {WEB}")
    print(f"Open: {url}")
    print("Ctrl+C to stop")
    if not args.no_browser:
        webbrowser.open(url)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
