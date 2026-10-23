"""Case-insensitive English -> Georgian lookup over engeo/data/dictionary.json."""

import difflib
import json
from functools import lru_cache
from pathlib import Path

DATA_FILE = Path(__file__).resolve().parent / "data" / "dictionary.json"


def normalize(word):
    """Lower-case and collapse whitespace so "  Apple ", "APPLE" and "apple" match."""
    return " ".join(str(word).split()).casefold()


def base_forms(word):
    """Guess dictionary forms of an inflected word: "running" -> "run", "cities" -> "city"."""
    candidates = []

    def add(stem):
        if len(stem) >= 2 and stem not in candidates:
            candidates.append(stem)

    for suffix, replacement in (("ies", "y"), ("ied", "y"), ("es", ""), ("s", ""),
                                ("ed", ""), ("ed", "e"), ("ing", ""), ("ing", "e"),
                                ("er", ""), ("est", ""), ("ly", "")):
        if word.endswith(suffix) and len(word) > len(suffix) + 1:
            stem = word[: -len(suffix)]
            add(stem + replacement)
            if not replacement and len(stem) > 2 and stem[-1] == stem[-2]:
                add(stem[:-1])  # "stopped" -> "stop", "running" -> "run"
    return candidates


class Dictionary:
    def __init__(self, path=DATA_FILE):
        with open(path, encoding="utf-8") as f:
            self.entries = json.load(f)["entries"]
        self.index = {}  # normalized headword -> entries
        self.form_index = {}  # normalized irregular form ("broke") -> entries
        for entry in self.entries:
            for variant in entry["variants"]:
                self._add(self.index, variant, entry)
            for form in entry["forms"]:
                self._add(self.form_index, form, entry)

    @staticmethod
    def _add(index, key, entry):
        bucket = index.setdefault(normalize(key), [])
        if entry not in bucket:
            bucket.append(entry)

    def lookup(self, word):
        """Look up an English word, ignoring case.

        Returns a dict with "found", "match" ("exact", "irregular form",
        "base form" or None), the matched "results" and, when nothing is found,
        spelling "suggestions".
        """
        query = normalize(word)
        response = {"query": word, "found": False, "match": None, "results": [], "suggestions": []}
        if not query:
            return response

        results, match = self.index.get(query), "exact"
        if not results:
            results, match = self.form_index.get(query), "irregular form"
        if not results:
            match = "base form"
            for candidate in base_forms(query):
                results = self.index.get(candidate)
                if results:
                    break

        if results:
            response.update(found=True, match=match, results=[public(e) for e in results])
        else:
            response["suggestions"] = self.suggest(query)
        return response

    def suggest(self, word, limit=5):
        """Headwords spelled similarly to `word`, for "did you mean" hints."""
        return difflib.get_close_matches(normalize(word), self.index.keys(), n=limit, cutoff=0.75)


def public(entry):
    return {key: entry[key] for key in ("word", "forms", "meanings", "phrases", "notes")}


@lru_cache(maxsize=1)
def default_dictionary():
    return Dictionary()


def lookup(word):
    """Look up an English word in the bundled dictionary (case-insensitive)."""
    return default_dictionary().lookup(word)


def suggest(word, limit=5):
    return default_dictionary().suggest(word, limit)
