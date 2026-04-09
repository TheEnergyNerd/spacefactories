"""Tiny static server for the spacefactories directory.

Used by `.claude/launch.json` so the interactive viewer (viewer.html) can
load manifest.json and the per-part STL files via HTTP.
"""
import os
import sys
from http.server import HTTPServer, SimpleHTTPRequestHandler

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8001
ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)

class Handler(SimpleHTTPRequestHandler):
    def end_headers(self):
        # Permissive CORS so STL/manifest fetches always work in dev
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

print(f"Serving {ROOT} on http://127.0.0.1:{PORT}/")
HTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
