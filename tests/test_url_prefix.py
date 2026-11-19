"""Exercise public URLs and sessions at root and under configurable mount paths."""
import json
import re
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from club import create_app
from club.assessments import AssessmentParser
from club.config import APP_URL_PREFIX


def script_config(response, name):
    match = re.search(rf'<script id="{name}" type="application/json">(.*?)</script>',
                      response.get_data(as_text=True), re.S)
    return json.loads(match.group(1))


class PrefixTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        manifest = {
            'id': 'demo', 'title': 'Prefix fixture', 'number_of_attempts': 0,
            'questions': [{'id': 'double', 'response_type': 'code_editor',
                'response_config': {'supported_languages': ['python'], 'grader': {
                    'code': 'def grade(ctx): ctx.check("21\\n", "42", points=100)',
                    'max_score': 100}}}],
        }
        (self.root/'assessment.json').write_text(json.dumps(manifest))
        item = AssessmentParser(self.root).load('assessment.json')
        patcher = patch('club.routes.parser.load_all', return_value=[item])
        patcher.start()
        self.addCleanup(patcher.stop)

    def app(self, prefix=None):
        config = {'TESTING': True, 'SECRET_KEY': 'prefix-test',
                  'ATTEMPT_DATABASE': self.root/'attempts.sqlite3'}
        if prefix is not None:
            config['APP_URL_PREFIX'] = prefix
        return create_app(config)

    def test_default_prefix_and_trailing_slash_redirect(self):
        with patch.dict('os.environ', {}, clear=True):
            self.assertEqual(self.app().config['APP_URL_PREFIX'], APP_URL_PREFIX)
            app = self.app('/tryouts')
        self.assertEqual(app.config['APP_URL_PREFIX'], '/tryouts')
        client = app.test_client()
        response = client.get('/tryouts')
        self.assertEqual(response.status_code, 308)
        self.assertTrue(response.location.endswith('/tryouts/'))
        for path in ['/', '/api/assignments', '/static/home.js', '/editor']:
            self.assertEqual(client.get(path).status_code, 404)

    def test_pages_assets_and_generated_urls_for_each_mount(self):
        for supplied, prefix in [('/tryouts', '/tryouts'), ('/club/tryouts/', '/club/tryouts'), ('', ''), ('/', '')]:
            with self.subTest(prefix=supplied):
                app = self.app(supplied)
                client = app.test_client()
                response = client.get(prefix+'/')
                self.assertEqual(response.status_code, 200)
                self.assertIn('Path='+(prefix or '/'), response.headers['Set-Cookie'])
                home = script_config(response, 'home-config')
                self.assertEqual(home['assignmentsUrl'], prefix+'/api/assignments')
                self.assertEqual(set(client.get(home['assignmentsUrl']).json), {'demo'})
                self.assertIn(f'href="{prefix}/assessment/demo"', response.get_data(as_text=True))
                for page in [response, client.get(prefix+'/assessment/demo'), client.get(prefix+'/editor')]:
                    self.assertEqual(page.status_code, 200)
                    for url in re.findall(r'(?:href|src)="([^"#]+)"', page.get_data(as_text=True)):
                        if url.startswith('https://'):
                            continue
                        self.assertTrue(url.startswith(prefix+'/'), url)
                        with client.get(url) as linked_response:
                            self.assertEqual(linked_response.status_code, 200, url)
                for suffix in ['/assessment/demo', '/editor']:
                    config = script_config(client.get(prefix+suffix), 'assessment-config')
                    self.assertEqual(config['baseUrl'], prefix)
                    self.assertEqual(config['homeUrl'], prefix+'/')
                    self.assertEqual(config['runUrl'], prefix+'/run')
                config = script_config(client.get(prefix+'/assessment/demo'), 'assessment-config')
                self.assertEqual(config['testsUrl'], prefix+'/assessment/demo/run-tests')
                self.assertEqual(config['attemptUrl'], prefix+'/api/assessment/demo/attempt')

    def test_attempt_save_grade_submit_and_execution_apis(self):
        client = self.app('/tryouts').test_client()
        config = script_config(client.get('/tryouts/assessment/demo'), 'assessment-config')
        response = client.post(config['attemptUrl'], json={})
        self.assertEqual(response.status_code, 200)
        attempt = response.json['attempt']
        url = config['baseUrl']+'/api/attempt/'+attempt['id']
        code = 'print(int(input()) * 2)'
        answers = {'double': {'python': code}}
        self.assertEqual(client.post(url, json={'answers': answers}).status_code, 200)
        self.assertEqual(client.get(url).json['attempt']['answers'], answers)
        self.assertEqual(client.post(config['runUrl'], json={
            'language': 'python', 'code': code, 'input': '21\n'}).json['output'].strip(), '42')
        result = client.post(config['testsUrl'], json={
            'language': 'python', 'code': code, 'question_id': 'double', 'attempt_id': attempt['id']})
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.json['passed'], 1)
        self.assertEqual(client.post('/tryouts/api/diagnostics', json={
            'language': 'python', 'code': 'print(42)'}).status_code, 200)
        with patch('club.interactive.start_program', return_value='terminal-id'):
            self.assertEqual(client.post('/tryouts/api/terminal', json={
                'language': 'python', 'code': code}).json, {'id': 'terminal-id'})
        for method in [client.get, client.post]:
            response = method('/tryouts/api/terminal/missing')
            self.assertEqual(response.status_code, 404)
            self.assertEqual(response.json['error'], 'Program not found')
        self.assertEqual(client.post(url, json={'submit': True, 'answers': answers}).status_code, 200)
        self.assertIsNotNone(client.get(url).json['attempt']['submitted'])

    def test_environment_override_and_invalid_prefixes(self):
        with patch.dict('os.environ', {'APP_URL_PREFIX': '/custom'}):
            self.assertEqual(self.app().config['APP_URL_PREFIX'], '/custom')
            self.assertEqual(self.app('').config['APP_URL_PREFIX'], '')
        for prefix in ['https://example.com', '/tryouts?x=1', '/a/../b', '/a//b', '/a b']:
            with self.subTest(prefix=prefix), self.assertRaises(ValueError):
                self.app(prefix)


if __name__ == '__main__':
    unittest.main()
