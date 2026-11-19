import json
import re
import subprocess
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from club import create_app
from club.config import MAX_CODE_LENGTH, MAX_OUTPUT_LENGTH


class AppTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.app = create_app({'TESTING': True, 'SECRET_KEY': 'test-only', 'ATTEMPT_DATABASE': Path(self.temp.name) / 'attempts.sqlite3'})
        self.client = self.app.test_client()
        from club.routes import parser
        # Build isolated regression fixtures in the test's temporary directory.
        # No example assessments are installed or exposed by the application.
        from club.assessments import AssessmentParser
        fixtures = []
        for timed in (False, True):
            item = {'id': 'timed_programming' if timed else 'practice_programming',
                    'title': 'Regression fixture', 'time_limit_seconds': 1800 if timed else 0,
                    'number_of_attempts': 1 if timed else 0,
                    'stimuli': {'instructions': 'Instructions'},
                    'questions': [{'id': 'instructions', 'response_type': 'stimulus_only', 'stimulus': 'instructions'}]}
            if timed:
                item['questions'].append({'id': 'student', 'response_type': 'short_answer', 'response_config': {'fields': [{'id': 'name', 'question_text': 'Name'}, {'id': 'email', 'question_text': 'Email'}]}})
            for number in range(5):
                item['questions'].append({'id': 'greeting' if number == 0 else f'q{number}',
                    'response_type': 'code_editor', 'response_config': {
                        'supported_languages': ['python'], 'grader': {
                            'code': 'def grade(ctx): ctx.check("", "Hello, world!")', 'max_score': 1}}})
            name = item['id'] + '.json'
            (Path(self.temp.name) / name).write_text(json.dumps(item), encoding='utf-8')
            fixtures.append(AssessmentParser(self.temp.name).load(name))
        patcher = patch('club.routes.parser.load_all', return_value=fixtures)
        patcher.start()
        self.addCleanup(patcher.stop)

    def begin(self, assessment='practice_programming', client=None):
        response = (client or self.client).post(f'/api/assessment/{assessment}/attempt', json={})
        self.assertEqual(response.status_code, 200)
        return response.json['attempt']

    def test_home_is_compact_and_editor_hidden(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(b'href="/editor"', response.data)
        self.assertNotIn(b'Export submitted', response.data)
        self.assertNotIn(b'next_squares', response.data)
        self.assertIn(b'Attempts: unlimited, No Time Limit', response.data)
        self.assertIn(b'Time Limit: 30:00', response.data)
        self.assertEqual(self.client.get('/export/submissions.csv').status_code, 404)

    def test_editor_and_assessment_share_workspace(self):
        html = self.client.get('/editor').get_data(as_text=True)
        config = json.loads(re.search(r'<script id="assessment-config" type="application/json">(.*?)</script>', html).group(1))
        self.assertTrue(config['standalone'])
        self.assertFalse(config['stimuliHtml'])
        self.assertEqual(set(config['languages']), {'python', 'java', 'cpp'})
        self.assertEqual(config['runUrl'], '/run')
        self.assertIn('Hello, world!', config['languages']['python']['default_code'])
        self.assertIn('question-select', html)

    def test_exactly_two_samples_and_correct_question_types(self):
        from club.routes import parser
        items = parser.load_all()
        self.assertEqual(len(items), 2)
        self.assertEqual([len(x['questions']) for x in items], [6, 7])
        self.assertEqual(items[0]['questions'][0]['response_type'], 'stimulus_only')
        self.assertEqual(items[1]['questions'][1]['response_type'], 'short_answer')
        self.assertNotIn('stimulus', items[1]['questions'][1])
        for item in items:
            self.assertEqual(sum(q['response_type'] == 'code_editor' for q in item['questions']), 5)

    def test_python_execution(self):
        response = self.client.post('/run', json={'language': 'python', 'code': 'print(6 * 7)'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {'output': '42\n'})
        response = self.client.post('/run', json={'language': 'python', 'code': 'print(input())', 'input': 'hello\n'})
        self.assertEqual(response.json, {'output': 'hello\n'})

    def test_invalid_requests(self):
        for data in [[], {}, {'language': []}, {'language': 'ruby', 'code': ''}, {'language': 'python', 'code': None}, {'language': 'python', 'code': 'x' * (MAX_CODE_LENGTH + 1)}]:
            with self.subTest(data=data if len(str(data)) < 100 else 'long code'):
                self.assertEqual(self.client.post('/run', json=data).status_code, 400)
        self.assertEqual(self.client.post('/run', data='bad JSON', content_type='application/json').status_code, 400)
        self.assertEqual(self.client.post('/run', json={'language': 'python', 'code': '', 'input': []}).status_code, 400)

    def test_timeout_and_missing_compiler(self):
        for error, expected in [(subprocess.TimeoutExpired('python', 5), 'timed out'), (FileNotFoundError(2, 'Missing compiler', 'javac'), 'javac')]:
            with patch('club.routes.run_code', side_effect=error):
                response = self.client.post('/run', json={'language': 'java', 'code': ''})
                self.assertIn(expected, response.json['output'])

    def test_output_limit(self):
        response = self.client.post('/run', json={'language': 'python', 'code': "print('x' * 11000)"})
        self.assertEqual(len(response.json['output']), MAX_OUTPUT_LENGTH)

    def test_server_resume_submit_limit_and_forged_score(self):
        attempt = self.begin('timed_programming')
        self.assertEqual(self.begin('timed_programming')['id'], attempt['id'])
        url = f'/api/attempt/{attempt["id"]}'
        data = self.client.post(url, json={'answers': {'student:name': 'Test Student'}, 'started': time.time() + 500000, 'score': {'fake': 100}, 'submit': True}).json['attempt']
        self.assertEqual(data['started'], attempt['started'])
        self.assertEqual(data['answers']['student:name'], 'Test Student')
        self.assertEqual(data['score'], {})
        self.assertTrue(data['submitted'])
        self.assertEqual(self.client.post('/api/assessment/timed_programming/attempt', json={}).status_code, 403)
        data2 = self.client.post(url, json={'answers': {'student:name': 'Changed'}}).json['attempt']
        self.assertEqual(data2['answers']['student:name'], 'Test Student')
        status = self.client.get('/api/assignments').json['timed_programming']
        self.assertEqual(status, {'count': 1, 'active': False, 'available': False})

    def test_attempt_ownership(self):
        attempt = self.begin()
        other = self.app.test_client()
        response = other.get(f'/api/attempt/{attempt["id"]}', headers={'User-Agent': 'Another device'})
        self.assertEqual(response.status_code, 404)

    def test_cookie_recovery_and_restart(self):
        attempt = self.begin('timed_programming')
        self.client.post(f'/api/attempt/{attempt["id"]}', json={'submit': True, 'answers': {}})
        other_app = create_app(self.app.config)
        other = other_app.test_client()
        status = other.get('/api/assignments').json['timed_programming']
        self.assertFalse(status['available'])
        self.assertEqual(status['count'], 1)

    def test_matching_network_browser_never_unlocks_private_answers(self):
        attempt = self.begin('timed_programming')
        self.client.post(f'/api/attempt/{attempt["id"]}', json={'answers': {'student:email': 'private@example.test'}})
        cookie_cleared = self.app.test_client()
        self.assertEqual(cookie_cleared.get(f'/api/attempt/{attempt["id"]}').status_code, 404)
        status = cookie_cleared.get('/api/assignments').json['timed_programming']
        self.assertFalse(status['active'])
        self.assertFalse(status['available'])
        self.assertEqual(cookie_cleared.post('/api/assessment/timed_programming/attempt', json={}).status_code, 403)

    def test_deadline_server_enforced_and_late_edits_rejected(self):
        attempt = self.begin('timed_programming')
        url = f'/api/attempt/{attempt["id"]}'
        self.client.post(url, json={'answers': {'student:name': 'Before'}})
        with patch('club.store.time.time', return_value=attempt['deadline'] + 10):
            data = self.client.post(url, json={'answers': {'student:name': 'After'}}).json['attempt']
            self.assertEqual(data['answers']['student:name'], 'Before')
            self.assertEqual(data['submitted'], attempt['deadline'])
            self.assertEqual(data['reason'], 'timeout')

    def test_hidden_test_answers_not_sent(self):
        html = self.client.get('/assessment/practice_programming').get_data(as_text=True)
        config = json.loads(re.search(r'<script id="assessment-config" type="application/json">(.*?)</script>', html).group(1))
        for q in config['assessment']['questions']:
            self.assertNotIn('grader', q['response_config'])
        self.assertNotIn('passcode', config['assessment'])

    def test_server_scoring_and_invalidation(self):
        attempt = self.begin()
        code = 'print("Hello, world!")'
        response = self.client.post('/assessment/practice_programming/run-tests', json={'attempt_id': attempt['id'], 'question_id': 'greeting', 'language': 'python', 'code': code})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['passed'], 1)
        saved = self.client.get(f'/api/attempt/{attempt["id"]}').json['attempt']
        self.assertEqual(saved['score']['greeting']['earned'], 1)
        saved = self.client.post(f'/api/attempt/{attempt["id"]}', json={'answers': {'greeting': {'python': 'print(0)'}}}).json['attempt']
        self.assertEqual(saved['score'], {})

    def test_cross_origin_and_remote_runner_denied(self):
        self.assertEqual(self.client.post('/api/assessment/practice_programming/attempt', json={}, headers={'Origin': 'https://attacker.example'}).status_code, 403)
        self.assertEqual(self.client.post('/run', json={'language': 'python', 'code': ''}, environ_overrides={'REMOTE_ADDR': '192.0.2.1'}).status_code, 503)

    def test_diagnostics_do_not_execute(self):
        data = self.client.post('/api/diagnostics', json={'language': 'python', 'code': 'print('}).json
        self.assertEqual(data['markers'][0]['severity'], 'error')
        data = self.client.post('/api/diagnostics', json={'language': 'python', 'code': 'import math\nraise Exception("must not execute")'}).json
        self.assertIn('not used', data['markers'][0]['message'])

    def test_interactive_input_and_eof(self):
        response = self.client.post('/api/terminal', json={'language': 'python', 'code': 'name = input("Name: ")\nprint("Hello, " + name)\nprint(len(input()))'})
        self.assertEqual(response.status_code, 200)
        url = f'/api/terminal/{response.json["id"]}'
        def wait_for(predicate):
            deadline = time.monotonic() + 5
            while time.monotonic() < deadline:
                result = self.client.get(url).json
                if predicate(result): return result
                time.sleep(.03)
            self.fail('Interactive program did not reach expected state')
        wait_for(lambda r: 'Name:' in r['output'])
        self.assertEqual(self.client.post(url, json={'input': 'Ada\n'}).status_code, 200)
        wait_for(lambda r: 'Hello, Ada' in r['output'])
        self.client.post(url, json={'input': '\n'})
        result = wait_for(lambda r: r['done'])
        self.assertIn('Name: Ada\nHello, Ada\n', result['output'])
        self.assertIn('Process exited 0', result['output'])

    def test_grader_cannot_overwrite_newer_draft(self):
        attempt = self.begin()
        url = f'/api/attempt/{attempt["id"]}'
        def delayed_grader(*args):
            self.client.post(url, json={'answers': {'greeting': {'python': 'print("new draft")'}}})
            return {'earned': 1, 'maximum': 1, 'tests': [], 'assessment_score': None}
        with patch('club.grading.grade_response', side_effect=delayed_grader):
            response = self.client.post('/assessment/practice_programming/run-tests', json={'attempt_id': attempt['id'], 'question_id': 'greeting', 'language': 'python', 'code': 'print("old draft")'})
        self.assertEqual(response.status_code, 200)
        saved = self.client.get(url).json['attempt']
        self.assertEqual(saved['answers']['greeting']['python'], 'print("new draft")')
        self.assertEqual(saved['score'], {})

    def test_host_only_export(self):
        attempt = self.begin()
        self.client.post(f'/api/attempt/{attempt["id"]}', json={'submit': True, 'answers': {}})
        output = Path(self.temp.name) / 'export.csv'
        result = self.app.test_cli_runner().invoke(args=['export-submissions', '--output', str(output)])
        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn(attempt['id'], output.read_text(encoding='utf-8'))


if __name__ == '__main__':
    unittest.main()
