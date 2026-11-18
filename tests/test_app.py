import json
import re
import subprocess
import unittest
from unittest.mock import patch

from club import create_app
from club.config import MAX_CODE_LENGTH, MAX_OUTPUT_LENGTH


class AppTests(unittest.TestCase):
    def setUp(self):
        self.client = create_app().test_client()

    def test_home_links_to_editor(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'href="/editor"', response.data)

    def test_editor_renders_problem_and_python_language_configuration(self):
        response = self.client.get("/editor")
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        config = json.loads(re.search(
            r'<script id="editor-config" type="application/json">(.*?)</script>', html
        ).group(1))
        self.assertEqual(set(config["languages"]), {"python", "java", "cpp"})
        self.assertEqual(config["runUrl"], "/run")
        self.assertIn("Hello, world!", config["languages"]["python"]["default_code"])
        self.assertIn('<div class="problem-content">', html)
        with self.client.get("/static/script.js") as script:
            self.assertEqual(script.status_code, 200)

    def test_python_execution(self):
        response = self.client.post("/run", json={"language": "python", "code": "print(6 * 7)"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {"output": "42\n"})

    def test_invalid_submissions(self):
        for data in [[], {}, {"language": []}, {"language": "ruby", "code": ""},
                     {"language": "python", "code": None},
                     {"language": "python", "code": "x" * (MAX_CODE_LENGTH + 1)}]:
            with self.subTest(data_type=type(data)):
                self.assertEqual(self.client.post("/run", json=data).status_code, 400)
        self.assertEqual(self.client.post("/run", data="bad JSON", content_type="application/json").status_code, 400)

    def test_timeout_and_missing_compiler(self):
        for error, expected in [
            (subprocess.TimeoutExpired("python", 5), "timed out"),
            (FileNotFoundError(2, "Missing compiler", "javac"), "javac"),
        ]:
            with patch("club.routes.run_code", side_effect=error):
                response = self.client.post("/run", json={"language": "java", "code": ""})
                self.assertIn(expected, response.json["output"])

    def test_output_limit(self):
        response = self.client.post("/run", json={"language": "python", "code": "print('x' * 11000)"})
        self.assertEqual(len(response.json["output"]), MAX_OUTPUT_LENGTH)


if __name__ == "__main__":
    unittest.main()
