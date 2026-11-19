import json
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer

from engeo.server import ENDPOINTS, Handler

Handler.log_message = lambda *args: None  # keep test output quiet


class ServerTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()
        cls.base = f"http://127.0.0.1:{cls.server.server_port}"
        cls.opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def get(self, path):
        try:
            with self.opener.open(self.base + path) as response:
                return response.status, json.load(response)
        except urllib.error.HTTPError as error:
            return error.code, json.load(error)

    def test_root_describes_every_endpoint_and_its_data_source(self):
        status, body = self.get("/")
        self.assertEqual(status, 200)
        self.assertEqual(body["endpoints"], ENDPOINTS)
        self.assertIn("dictionary.json", body["data_source"])
        for endpoint in body["endpoints"].values():
            self.assertTrue(endpoint["description"])
            self.assertTrue(endpoint["data_source"])

    def test_health_reports_loaded_data(self):
        status, body = self.get("/health")
        self.assertEqual(status, 200)
        self.assertEqual(body["entries"], 8658)
        self.assertEqual(body["data_file"], "engeo/data/dictionary.json")
        self.assertTrue(body["source"].endswith(".pdf"))

    def test_lookup_query_and_path_forms(self):
        for path in ("/lookup?word=WATER", "/lookup/water"):
            status, body = self.get(path)
            self.assertEqual(status, 200)
            self.assertEqual(body["results"][0]["meanings"], ["წყალი", "მორწყვა"])

    def test_lookup_errors(self):
        self.assertEqual(self.get("/lookup?word=")[0], 400)
        status, body = self.get("/lookup/aple")
        self.assertEqual(status, 404)
        self.assertIn("apple", body["suggestions"])

    def test_unknown_endpoint_lists_endpoints(self):
        status, body = self.get("/nope")
        self.assertEqual(status, 404)
        self.assertEqual(body["endpoints"], list(ENDPOINTS))


if __name__ == "__main__":
    unittest.main()
