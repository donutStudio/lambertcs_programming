import json
from contextlib import closing
import sqlite3
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from club import create_app
from club.assessments import AssessmentParser
from club.final_grading import grade_next
from club.grading import grade_response
from club.store import database


class AssessmentFlowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.manifest = {
            'id': 'demo', 'title': 'Demo', 'number_of_attempts': 1,
            'required_credentials': ['full_name', 'email', 'student_id'],
            'questions': [{'id': key, 'response_type': 'code_editor', 'response_config': {
                'supported_languages': ['python'], 'runnable_tests': False,
                'grader': {'code': 'def grade(ctx): ctx.check("21\\n", "42", points=10)', 'max_score': 10}}}
                for key in ('first', 'last')],
        }
        self.load()
        self.app = create_app({'TESTING': True, 'SECRET_KEY': 'test', 'APP_URL_PREFIX': '',
                               'ATTEMPT_DATABASE': self.root / 'attempts.sqlite3'})
        self.client = self.app.test_client()
        self.credentials = {'full_name': 'Jane Doe', 'email': 'jane@example.com', 'student_id': '12345'}
        self.patcher = patch('club.routes.parser.load_all', side_effect=lambda: [self.item])
        self.patcher.start(); self.addCleanup(self.patcher.stop)

    def load(self):
        (self.root / 'assessment.json').write_text(json.dumps(self.manifest))
        self.item = AssessmentParser(self.root).load('assessment.json')

    def begin(self, client=None):
        return (client or self.client).post('/api/assessment/demo/attempt', json={'credentials': self.credentials})

    def test_shared_network_isolation_and_idempotent_resume(self):
        one = self.begin().json['attempt']
        two = self.begin(self.app.test_client()).json['attempt']
        self.assertNotEqual(one['id'], two['id'])
        self.assertEqual(one['id'], self.begin().json['attempt']['id'])
        self.assertEqual(self.client.get('/api/assignments').json['demo']['count'], 1)
        self.client.post('/api/attempt/' + one['id'], json={'submit': True})
        self.assertEqual(self.begin().status_code, 403)
        stranger = self.app.test_client()
        self.assertEqual(stranger.get('/api/attempt/' + one['id']).status_code, 404)
        self.assertEqual(self.begin(stranger).status_code, 200)

    def test_credentials_validated_before_passcode(self):
        self.item['passcode'] = 'secret'
        response = self.client.post('/api/assessment/demo/attempt', json={})
        self.assertEqual(response.status_code, 400)
        self.assertNotIn('passcode', response.json['error'])
        for key, value in [('email', 'bad'), ('student_id', 'abc'), ('full_name', ' ')]:
            credentials = dict(self.credentials, **{key: value})
            self.assertEqual(self.client.post('/api/assessment/demo/attempt', json={'credentials': credentials, 'passcode': 'secret'}).status_code, 400)
        response = self.client.post('/api/assessment/demo/attempt', json={'credentials': self.credentials, 'passcode': 'secret'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.post('/api/assessment/demo/attempt', json={}).status_code, 200)

    def test_final_grading_runs_all_and_updates_visible_score(self):
        attempt = self.begin().json['attempt']
        code = 'print(int(input("a completely different prompt: ")) * 2)'
        answers = {key: {'python': code} for key in ('first', 'last')}
        url = '/api/attempt/' + attempt['id']
        response = self.client.post(url, json={'answers': answers, 'languages': {'first': 'python', 'last': 'python'}, 'submit': True})
        self.assertEqual(response.json['attempt']['grading_status'], 'pending')
        self.assertEqual(self.client.get('/api/assignments').json['demo']['score'], 'waiting')
        self.assertTrue(grade_next(self.app))
        final = self.client.get(url).json['attempt']
        self.assertEqual(final['grading_status'], 'complete')
        self.assertEqual(final['score']['first']['earned'], 10)
        self.assertEqual(final['score']['last']['earned'], 10)
        self.assertEqual(self.client.get('/api/assignments').json['demo']['score'], '20/20')
        self.assertFalse(grade_next(self.app))
        self.assertEqual(self.client.post(url, json={'submit': True, 'answers': {}}).json['attempt']['answers'], answers)

    def test_timeout_grades_without_client_and_one_failure_does_not_skip_others(self):
        self.item['questions'][0]['response_config']['grader']['code'] = 'def grade(ctx): raise ValueError("broken grader")'
        attempt = self.begin().json['attempt']
        with self.app.app_context(), database() as db:
            db.execute('UPDATE attempts SET deadline=?, answers=? WHERE id=?', (time.time()-1, json.dumps({'last': {'python': 'print(42)'}}), attempt['id']))
        with self.assertLogs(self.app.logger, level='ERROR'):
            self.assertTrue(grade_next(self.app))
        final = self.client.get('/api/attempt/' + attempt['id']).json['attempt']
        self.assertEqual(final['reason'], 'timeout')
        self.assertEqual(final['grading_status'], 'error')
        self.assertEqual(final['score']['last']['earned'], 10)

    def test_active_attempt_keeps_original_definition_after_edits(self):
        attempt = self.begin().json['attempt']
        self.item['title'] = 'Changed title'
        self.item['questions'] = []
        response = self.client.get('/assessment/demo')
        self.assertIn('Demo', response.get_data(as_text=True))
        url = '/api/attempt/' + attempt['id']
        answers = {'first': {'python': 'print(42)'}, 'last': {'python': 'print(42)'}}
        self.client.post(url, json={'answers': answers, 'submit': True})
        self.assertTrue(grade_next(self.app))
        self.assertEqual(self.client.get(url).json['attempt']['score']['first']['earned'], 10)

    def test_python_prompts_ignored_but_actual_wrong_output_fails(self):
        grader = {'code': 'def grade(ctx): ctx.check("1\\n2\\n", "3", points=1)', 'max_score': 1}
        correct = 'a=int(input("First: ")); b=int(input("Other: ")); print(a+b)'
        self.assertEqual(grade_response('python', correct, grader, {})['earned'], 1)
        self.assertEqual(grade_response('python', correct + '; print("extra")', grader, {})['earned'], 0)

    def test_admin_without_site_packages_filters_backup_and_scoped_reset(self):
        one = self.begin().json['attempt']
        other = self.begin(self.app.test_client()).json['attempt']
        with self.app.app_context(), database() as db:
            owner = db.execute('SELECT owner FROM attempts WHERE id=?', (one['id'],)).fetchone()[0]
        script = Path(__file__).resolve().parents[1] / 'admin_tools.py'
        def admin(*args):
            result = subprocess.run([sys.executable, '-S', str(script), '--database', str(self.root / 'attempts.sqlite3'), *args], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            return result.stdout
        self.assertIn(one['id'], admin('list', '--email', 'JANE@EXAMPLE.COM'))
        csv = self.root / 'export.csv'
        admin('export', '--since', '2026-11-19T11:50:00-05:00', '--output', str(csv))
        self.assertIn('student_id', csv.read_text())
        backup = self.root / 'backup.sqlite3'
        admin('backup', '--output', str(backup))
        with closing(sqlite3.connect(backup)) as db:
            self.assertEqual(db.execute('SELECT count(*) FROM attempts').fetchone()[0], 2)
        admin('reset-device', owner, '--confirm')
        self.assertNotIn(one['id'], admin('list'))
        self.assertIn(other['id'], admin('list'))


if __name__ == '__main__': unittest.main()
