import unittest

from engeo import lookup
from engeo.__main__ import main


class LookupTest(unittest.TestCase):
    def test_case_insensitive(self):
        for query in ("apple", "Apple", "APPLE", "  aPPle  "):
            result = lookup(query)
            self.assertTrue(result["found"], query)
            self.assertEqual(result["results"][0]["meanings"], ["ვაშლი"])

    def test_multiple_meanings_and_phrases(self):
        entry = lookup("break")["results"][0]
        self.assertEqual(entry["forms"], ["broke", "broken"])
        self.assertEqual(len(entry["meanings"]), 2)
        self.assertIn({"en": "break down", "ka": "ჩაშლა"}, entry["phrases"])

    def test_variants(self):
        self.assertEqual(lookup("jiffy")["results"][0]["word"], "jiff(y)")
        self.assertEqual(lookup("academical")["results"][0]["meanings"], ["აკადემიური"])

    def test_wrapped_headword(self):
        entry = lookup("underwrite")["results"][0]
        self.assertEqual(entry["forms"], ["underwrote", "underwritten"])

    def test_inflected_forms(self):
        self.assertEqual(lookup("running")["match"], "base form")
        self.assertEqual(lookup("running")["results"][0]["word"], "run")
        self.assertEqual(lookup("cities")["results"][0]["word"], "city")
        self.assertEqual(lookup("misled")["match"], "irregular form")

    def test_not_found_suggests(self):
        result = lookup("aple")
        self.assertFalse(result["found"])
        self.assertIn("apple", result["suggestions"])

    def test_empty_query(self):
        self.assertFalse(lookup("   ")["found"])

    def test_cli_exit_code(self):
        self.assertEqual(main(["Water"]), 0)
        self.assertEqual(main(["qwertyuiop"]), 1)


if __name__ == "__main__":
    unittest.main()
