"""Convert the English-Georgian dictionary PDF into engeo/data/dictionary.json.

The PDF uses the legacy Geo_Times font: Georgian letters are stored as Latin-1
characters (e.g. "ÀÍÁÀÍÉ" is "ანბანი"), so extracted text is remapped to
Georgian Unicode before parsing.

Requires `pdftotext` (poppler-utils). Usage:

    python tools/build_dictionary.py [path/to/dictionary.pdf]
"""

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PDF = ROOT / "ინგლისურ-ქართული-ლექსიკონი.pdf"
OUTPUT = ROOT / "engeo" / "data" / "dictionary.json"

# Geo_Times / Acad-style 8-bit layout: 0xC0.. maps to the Georgian alphabet in order.
LEGACY = "ÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖ×ØÙÚÛÜÝÞßàáâãä"
GEORGIAN = "აბგდევზჱთიკლმნჲოპჟრსტჳუფქღყშჩცძწჭხჴჯჰ"
LEGACY_TABLE = str.maketrans(LEGACY, GEORGIAN)

GEO_CHAR = re.compile("[ა-ჿ]")
GAP = re.compile(r"\s{2,}")
# A dash touching a space or the line end marks an English phrase ("at play- ...",
# "account of - ..."), which continues the previous entry rather than starting one.
PHRASE_DASH = re.compile(r"\s-|-\s|-$")
NUMBERED = re.compile(r"(?:^|\s)\d+\.\s*")
# English phrase starting right after Georgian text without a ";" ("... უცბად, all the same-...").
INLINE_PHRASE = re.compile(r"(?<=[ა-ჿ)])[\s,]+(?=[A-Za-z])")


def extract_text(pdf_path):
    result = subprocess.run(
        ["pdftotext", "-layout", str(pdf_path), "-"],
        check=True, capture_output=True, text=True, encoding="utf-8",
    )
    return result.stdout.translate(LEGACY_TABLE)


def split_head(line):
    """Split a line into (headword part, meaning part)."""
    gap = GAP.search(line)
    if gap and not GEO_CHAR.search(line[:gap.start()]):
        return line[:gap.start()].strip(), line[gap.end():].strip()
    geo = GEO_CHAR.search(line)
    if geo:
        return line[:geo.start()].strip(), line[geo.start():].strip()
    return line.strip(), ""


def group_entries(text):
    """Yield (headword, meaning) pairs, joining wrapped and continuation lines."""
    section = None
    head, meaning = None, []
    for raw in text.splitlines():
        line = raw.replace("\f", "").strip()
        if not line:
            continue
        if len(line) == 1 and line.isupper() and raw.replace("\f", "")[:1].isspace():
            section = line.lower()  # centred letter heading
            continue
        word, rest = split_head(line)
        if head and not meaning and (head.count("(") > head.count(")") or head.endswith(",")):
            # headword wrapped over lines: "underwrite," / "(underwrote," / "underwritten) ..."
            head = f"{head} {word}"
            meaning = [rest] if rest else []
            continue
        starts_entry = (
            line[0].isascii() and line[0].isalpha()
            and not PHRASE_DASH.search(word)
            and (section is None or word[:1].lower() == section)
        )
        if starts_entry:
            if head:
                yield head, " ".join(meaning)
            head, meaning = word, [rest] if rest else []
        elif head:
            meaning.append(line)
    if head:
        yield head, " ".join(meaning)


def split_top_level(text, sep):
    """Split on `sep` outside parentheses."""
    parts, depth, current = [], 0, []
    for ch in text:
        depth += ch == "("
        depth -= ch == ")" and depth > 0
        if ch == sep and depth == 0:
            parts.append("".join(current))
            current = []
        else:
            current.append(ch)
    parts.append("".join(current))
    return [p.strip(" ,") for p in parts if p.strip(" ,")]


def parse_headword(head):
    """Return (display word, lookup variants, irregular forms)."""
    forms = []
    m = re.match(r"^(.*?)\s*\(([^)]*,[^)]*)\)\s*$", head)
    if m:  # "bid (bade, bid, bidden)"
        head = m.group(1)
        forms = [f.strip() for f in re.split(r"[,\s]+", m.group(2)) if f.strip()]
    variants = []
    for part in re.split(r"[;,]", head):
        part = " ".join(part.split())
        if not part:
            continue
        opt = re.match(r"^(.*)\(([a-z]+)\)$", part)
        if opt:  # "jiff(y)" -> jiff, jiffy
            variants += [opt.group(1), opt.group(1) + opt.group(2)]
        else:
            variants.append(part)
    return head.strip(" ;,"), variants, forms


def parse_meaning(text):
    """Split meaning text into Georgian meanings, English phrases and notes."""
    forms = []
    m = re.match(r"^\(([A-Za-z ,]+)\)\s*", text)
    if m:  # meaning line starting with irregular forms: "(misled, misled) ..."
        forms = [f for f in re.split(r"[,\s]+", m.group(1)) if f]
        text = text[m.end():]

    meanings, phrases, notes = [], [], []
    for chunk in split_top_level(text, ";"):
        pieces = [p for n in NUMBERED.split(chunk) for p in INLINE_PHRASE.split(n)]
        for piece in pieces:
            piece = piece.strip(" ,")
            if not piece:
                continue
            geo = GEO_CHAR.search(piece)
            if not geo:
                notes.append(piece)
            elif piece[0].isascii() and piece[0].isalpha():
                en = piece[:geo.start()].strip().rstrip("-").strip()
                phrases.append({"en": en, "ka": piece[geo.start():].strip()})
            else:
                meanings.append(piece)
    return forms, meanings, phrases, notes


def build(pdf_path):
    entries = []
    for head, meaning_text in group_entries(extract_text(pdf_path)):
        word, variants, forms = parse_headword(head)
        extra_forms, meanings, phrases, notes = parse_meaning(meaning_text)
        entry = {"word": word, "variants": variants, "forms": forms + extra_forms,
                 "meanings": meanings, "phrases": phrases, "notes": notes,
                 "source": f"{head}  {meaning_text}".strip()}
        if meanings or phrases:
            entries.append(entry)
        else:
            print(f"skipped (no Georgian meaning): {entry['source']!r}", file=sys.stderr)
    return entries


def main():
    pdf = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_PDF
    entries = build(pdf)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump({"source": pdf.name, "entries": entries}, f, ensure_ascii=False, indent=1)
        f.write("\n")
    print(f"wrote {len(entries)} entries to {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
