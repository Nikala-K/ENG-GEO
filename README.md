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

**HTTP API**

```
$ python -m engeo serve --port 8000
GET http://127.0.0.1:8000/lookup?word=Water   -> 200 + JSON result
GET http://127.0.0.1:8000/lookup/Water        -> same
GET http://127.0.0.1:8000/health
```

Unknown words return `404` with `"found": false` and spelling `suggestions`.

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
