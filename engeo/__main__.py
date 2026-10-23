"""Command line:

    python -m engeo apple            # print Georgian meanings
    python -m engeo apple --json     # raw JSON result
    python -m engeo serve --port 8000
"""

import argparse
import json
import sys

from .dictionary import lookup


def format_result(result):
    if not result["found"]:
        lines = [f"'{result['query']}' not found."]
        if result["suggestions"]:
            lines.append("Did you mean: " + ", ".join(result["suggestions"]) + "?")
        return "\n".join(lines)
    lines = []
    for entry in result["results"]:
        header = entry["word"]
        if entry["forms"]:
            header += f" ({', '.join(entry['forms'])})"
        if result["match"] != "exact":
            header += f"  [{result['match']} of '{result['query']}']"
        lines.append(header)
        lines += [f"  {i}. {m}" for i, m in enumerate(entry["meanings"], 1)]
        lines += [f"  • {p['en']} — {p['ka']}" for p in entry["phrases"]]
    return "\n".join(lines)


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if argv and argv[0] == "serve":
        parser = argparse.ArgumentParser(prog="python -m engeo serve")
        parser.add_argument("--host", default="127.0.0.1")
        parser.add_argument("--port", type=int, default=8000)
        args = parser.parse_args(argv[1:])
        from .server import serve
        serve(args.host, args.port)
        return 0

    parser = argparse.ArgumentParser(prog="python -m engeo", description="English -> Georgian dictionary")
    parser.add_argument("word", nargs="+", help="English word (case-insensitive)")
    parser.add_argument("--json", action="store_true", help="print the raw JSON result")
    args = parser.parse_args(argv)
    sys.stdout.reconfigure(encoding="utf-8")
    result = lookup(" ".join(args.word))
    print(json.dumps(result, ensure_ascii=False, indent=2) if args.json else format_result(result))
    return 0 if result["found"] else 1


if __name__ == "__main__":
    sys.exit(main())
