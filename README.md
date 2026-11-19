# ENG-GEO — English → Georgian dictionary

Give an English word (any capitalisation), get its Georgian meaning(s).
8,658 entries converted from `ინგლისურ-ქართული-ლექსიკონი.pdf`.
Pure Python 3.9+, no dependencies — copy the repo and call it.

## Use it

**From Python**

```python
from engeo import lookup

lookup("Apple")
# {'query': 'Apple', 'found': True, 'match': 'exact',
#  'results': [{'word': 'apple', 'forms': [], 'meanings': ['ვაშლი'],
#               'phrases': [{'en': 'apple of the eye', 'ka': 'თვალის გუგა, თვალის ჩინი'}],
#               'notes': []}],
#  'suggestions': []}
```

**Command line**

```
$ python -m engeo BREAK
break (broke, broken)
  1. დამტვრევა, გატეხვა, დარღვევა (კანონის), გაკაფვა (გზის), გამოცხადება (ახალი ამბის)
  2. შენანგრევი, შესვენება
  • break down — ჩაშლა
  ...
$ python -m engeo apple --json      # same result as JSON
```

**HTTP API** — `python -m engeo serve --port 8000`

Read-only JSON over HTTP, GET only. **Where the data comes from:**
`ინგლისურ-ქართული-ლექსიკონი.pdf` → `tools/build_dictionary.py` →
`engeo/data/dictionary.json` (8,658 entries) → loaded into memory once at startup.
Every endpoint answers from that in-memory copy — no database, no external service, no
network calls. To change the data, rebuild or edit `dictionary.json` and restart the server.

| Endpoint | What it does | Responses |
|---|---|---|
| `GET /lookup?word=<word>` | Georgian meanings of one English word, case-insensitive (see Lookup rules) | `200` found · `400` word missing/blank · `404` not found, with `suggestions` |
| `GET /lookup/<word>` | Same, with the URL-encoded word in the path | same as above |
| `GET /health` | Liveness check; reports the loaded entry count and source file, without a lookup | `200` |
| `GET /` | This description as JSON: every endpoint, its data source, responses and an example | `200` |

Any other path returns `404` with the list of endpoints.

`/lookup` response:

```json
{
  "query": "Water",
  "found": true,
  "match": "exact",            // "exact" | "irregular form" | "base form" | null
  "results": [
    {
      "word": "water",          // headword as printed in the dictionary
      "forms": [],              // irregular forms, e.g. ["broke", "broken"]
      "meanings": ["წყალი", "მორწყვა"],   // one item per sense
      "phrases": [],            // [{"en": "break down", "ka": "ჩაშლა"}, ...]
      "notes": []               // English text the parser could not attach to a meaning
    }
  ],
  "suggestions": []             // similar headwords, only when found is false
}
```

`/health` response:

```json
{"status": "ok", "entries": 8658, "source": "ინგლისურ-ქართული-ლექსიკონი.pdf",
 "data_file": "engeo/data/dictionary.json"}
```

**Any other language** — read `engeo/data/dictionary.json` directly
(`entries[]` with `word`, `variants`, `forms`, `meanings`, `phrases`, `notes`, `source`).
Match on lower-cased `variants`.

## Lookup rules

1. Input is trimmed and lower-cased: `Apple`, `APPLE`, ` apple ` are the same.
2. Exact headword or variant (`jiffy` → `jiff(y)`, `academical` → `academic, academical`).
3. Irregular verb forms listed in the dictionary (`misled` → `mislead`).
4. Simple English endings (`running` → `run`, `cities` → `city`); `match` says which rule hit.
5. Otherwise: not found, with "did you mean" suggestions.

## Rebuilding the data

The PDF uses the legacy `Geo_Times` font, so its text is remapped to Georgian Unicode
during conversion. Requires `pdftotext` (poppler-utils):

```
python tools/build_dictionary.py            # writes engeo/data/dictionary.json
python -m unittest discover -s tests
```

Each entry keeps its original line in `source`, so parsing mistakes can be traced back.
Mistakes in the original dictionary (typos, misplaced lines) are carried over as-is.
