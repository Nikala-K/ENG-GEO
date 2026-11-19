"""Read-only JSON HTTP API for the English -> Georgian dictionary (standard library only).

Where the data comes from:
    ინგლისურ-ქართული-ლექსიკონი.pdf
      -> tools/build_dictionary.py   (remaps the PDF's legacy Geo_Times font to Georgian
                                      Unicode and parses it into entries)
      -> engeo/data/dictionary.json  (8,658 entries, committed to the repo)
      -> loaded into memory once at startup and indexed by lower-cased headword

Every request is answered from that in-memory copy: no database, no external service,
no network calls. The API never writes anything. To change the data, edit or rebuild
dictionary.json and restart the server.

Endpoints (GET only):
    GET /                       this API's description, as JSON
    GET /lookup?word=<word>     Georgian meanings of one English word
    GET /lookup/<word>          same, with the word in the path
    GET /health                 liveness check plus the loaded data's source and size
"""

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, unquote, urlparse

from .dictionary import DATA_FILE, default_dictionary

DATA_SOURCE = (
    "engeo/data/dictionary.json, converted from the English-Georgian dictionary PDF by "
    "tools/build_dictionary.py; loaded into memory at startup, no database or external calls"
)

# Served at GET / and used in the 404 hint, so the API describes itself.
ENDPOINTS = {
    "GET /lookup?word=<word>": {
        "description": (
            "Look up one English word and return its Georgian meanings, phrases and "
            "irregular forms. Case-insensitive; surrounding spaces are ignored."
        ),
        "data_source": DATA_SOURCE,
        "matching": [
            "exact headword or variant (jiffy -> jiff(y))",
            "irregular form listed in the dictionary (misled -> mislead)",
            "common English endings removed (running -> run, cities -> city)",
            "otherwise not found, with spelling suggestions",
        ],
        "responses": {
            "200": "found: results[] holds the matching entries; 'match' says which rule matched",
            "400": "the 'word' parameter is missing or blank",
            "404": "no entry: found=false and 'suggestions' lists similar headwords",
        },
        "example": "/lookup?word=Water",
    },
    "GET /lookup/<word>": {
        "description": "Same as /lookup?word=<word>, with the URL-encoded word in the path.",
        "data_source": DATA_SOURCE,
        "example": "/lookup/water",
    },
    "GET /health": {
        "description": (
            "Liveness check. Reports how many entries are loaded and which file they were "
            "converted from, without looking anything up."
        ),
        "data_source": "the in-memory dictionary loaded at startup",
        "responses": {"200": "status=ok, entries=<count>, source=<pdf name>, data_file=<path>"},
        "example": "/health",
    },
    "GET /": {
        "description": "This description of the API.",
        "data_source": "static, defined in engeo/server.py",
    },
}


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        url = urlparse(self.path)
        if url.path == "/":
            return self.describe()
        if url.path == "/health":
            return self.health()
        if url.path == "/lookup":
            return self.lookup(parse_qs(url.query).get("word", [""])[0])
        if url.path.startswith("/lookup/"):
            return self.lookup(unquote(url.path[len("/lookup/"):]))
        self.send_json(404, {"error": f"unknown endpoint {url.path}", "endpoints": list(ENDPOINTS)})

    def describe(self):
        """GET / — static description of every endpoint and where its data comes from."""
        self.send_json(200, {
            "name": "English-Georgian dictionary API",
            "data_source": DATA_SOURCE,
            "read_only": True,
            "endpoints": ENDPOINTS,
        })

    def health(self):
        """GET /health — confirms the server is up and reports the loaded data, no lookup."""
        dictionary = default_dictionary()
        self.send_json(200, {
            "status": "ok",
            "entries": len(dictionary.entries),
            "source": dictionary.source,
            "data_file": DATA_FILE.relative_to(DATA_FILE.parents[2]).as_posix(),
        })

    def lookup(self, word):
        """GET /lookup — answers from the in-memory index built from dictionary.json."""
        if not word.strip():
            return self.send_json(400, {"error": "missing 'word'", "example": "/lookup?word=apple"})
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
    default_dictionary()  # load dictionary.json into memory once, before accepting requests
    server = ThreadingHTTPServer((host, port), Handler)
    print(f"English-Georgian dictionary API on http://{host}:{port}/ (endpoint list at /)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
