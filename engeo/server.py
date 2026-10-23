"""Minimal JSON HTTP API (standard library only).

    GET /lookup?word=Apple   or   GET /lookup/Apple
    GET /health
"""

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, unquote, urlparse

from .dictionary import default_dictionary


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        url = urlparse(self.path)
        if url.path == "/health":
            return self.send_json(200, {"status": "ok", "entries": len(default_dictionary().entries)})
        if url.path == "/lookup":
            word = parse_qs(url.query).get("word", [""])[0]
        elif url.path.startswith("/lookup/"):
            word = unquote(url.path[len("/lookup/"):])
        else:
            return self.send_json(404, {"error": "use /lookup?word=<english word>"})
        if not word.strip():
            return self.send_json(400, {"error": "missing 'word'"})
        result = default_dictionary().lookup(word)
        self.send_json(200 if result["found"] else 404, result)

    def send_json(self, status, payload):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def serve(host="127.0.0.1", port=8000):
    default_dictionary()  # load once before accepting requests
    server = ThreadingHTTPServer((host, port), Handler)
    print(f"English-Georgian dictionary API on http://{host}:{port}/lookup?word=apple")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
