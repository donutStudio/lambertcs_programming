"""Reference configuration, lazy delivery, and assessment-specific access."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from zipfile import ZipFile

from club import create_app
from club.assessments import AssessmentParser
from club.references import BUILTIN_REFERENCES, reference_source, split_sections
from test_url_prefix import script_config


class ReferenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.manifest = {
            'id': 'demo', 'title': 'Reference fixture', 'questions': [],
            'reference_sheets': {
                'notes': {'name': 'Exam notes', 'content': '# Notes\n\n## First\n\nUse **meters**.\n\n## Last\n\nNeedle $x^2$.\n'},
                'private': {'name': 'Not allowed', 'content': 'DO NOT SHIP THIS'},
            },
            'allowed_reference_sheets': ['py_reference', 'notes'],
        }

    def load(self, manifest=None):
        (self.root/'assessment.json').write_text(json.dumps(manifest or self.manifest), encoding='utf-8')
        return AssessmentParser(self.root).load('assessment.json')

    def client(self, item, prefix=''):
        patcher = patch('club.routes.parser.load_all', return_value=[item])
        patcher.start(); self.addCleanup(patcher.stop)
        return create_app({'TESTING': True, 'SECRET_KEY': 'reference-tests',
                           'APP_URL_PREFIX': prefix,
                           'ATTEMPT_DATABASE': self.root/'attempts.sqlite3'}).test_client()

    def test_defaults_and_builtin_documents(self):
        item = self.load({'id': 'demo', 'questions': []})
        self.assertEqual(item['allowed_reference_sheets'], list(BUILTIN_REFERENCES))
        for key in BUILTIN_REFERENCES:
            source = reference_source(item, key)
            self.assertGreater(len(split_sections(source)), 8)
            self.assertIn('```', source)

    def test_inline_file_and_zip_content(self):
        manifest = copy.deepcopy(self.manifest)
        manifest['reference_sheets']['notes']['content'] = {'$file': 'notes.md'}
        source = '# File reference\n\n## Example\n\n```python\nprint("hello")\n```'
        (self.root/'notes.md').write_bytes(source.encode('utf-8'))
        self.assertEqual(self.load(manifest)['reference_sheets']['notes']['content'], source)
        with ZipFile(self.root/'bundle.zip', 'w') as bundle:
            bundle.writestr('bundle/assessment.json', json.dumps(manifest))
            bundle.writestr('bundle/notes.md', source)
        self.assertEqual(AssessmentParser(self.root).load('bundle.zip')['reference_sheets']['notes']['content'], source)

    def test_invalid_definitions(self):
        changes = [
            {'allowed_reference_sheets': ['missing']},
            {'allowed_reference_sheets': ['py_reference', 'py_reference']},
            {'allowed_reference_sheets': 'py_reference'},
            {'allowed_reference_sheets': [42]},
            {'reference_sheets': []},
            {'reference_sheets': {'py_reference': {'name': 'Override', 'content': 'no'}}},
            {'reference_sheets': {'../file': {'name': 'Bad', 'content': 'no'}}},
            {'reference_sheets': {'notes': {'name': '', 'content': 'no'}}},
            {'reference_sheets': {'notes': {'name': 'Notes', 'content': {}}}},
        ]
        for change in changes:
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.load({**self.manifest, **change})

    def test_file_reference_cannot_escape_bundle(self):
        manifest = copy.deepcopy(self.manifest)
        manifest['reference_sheets']['notes']['content'] = {'$file': '../outside.md'}
        with self.assertRaisesRegex(ValueError, 'inside'):
            self.load(manifest)

    def test_public_config_only_contains_allowed_metadata(self):
        client = self.client(self.load(), '/club/tryouts')
        with patch('club.routes.reference_source', side_effect=AssertionError('Eager reference read')):
            response = client.get('/club/tryouts/assessment/demo')
            self.assertEqual(response.status_code, 200)
        config = script_config(response, 'assessment-config')['assessment']
        self.assertNotIn('reference_sheets', config)
        self.assertEqual([r['name'] for r in config['references']], ['Python', 'Exam notes'])
        self.assertTrue(all(r['url'].startswith('/club/tryouts/api/') for r in config['references']))
        self.assertNotIn('DO NOT SHIP THIS', response.text)
        self.assertNotIn('Needle', response.text)
        self.assertIn('id="reference-toggle"', response.text)

    def test_empty_allowlist_hides_button_and_denies_reads(self):
        client = self.client(self.load({**self.manifest, 'allowed_reference_sheets': []}))
        self.assertNotIn('id="reference-toggle"', client.get('/assessment/demo').text)
        self.assertEqual(client.get('/api/assessment/demo/references/py_reference').status_code, 404)

    def test_metadata_and_single_section_delivery(self):
        client = self.client(self.load())
        url = '/api/assessment/demo/references/notes'
        metadata = client.get(url)
        self.assertEqual(metadata.json, {'sections': [
            {'id': 0, 'title': 'Overview'}, {'id': 1, 'title': 'First'}, {'id': 2, 'title': 'Last'}]})
        self.assertEqual(metadata.headers['Cache-Control'], 'no-store')
        first = client.get(url+'?section=1').json['html']
        self.assertIn('<strong>meters</strong>', first)
        self.assertNotIn('Needle', first)
        self.assertIn('data-math="x^2"', client.get(url+'?section=2').json['html'])
        for index in ['-1', '999', 'text']:
            self.assertEqual(client.get(url+'?section='+index).status_code, 404)

    def test_search_finds_unloaded_section_and_treats_input_literally(self):
        client = self.client(self.load())
        url = '/api/assessment/demo/references/notes'
        result = client.get(url, query_string={'q': 'nEeDlE'}).json['results']
        self.assertEqual(result[0]['section'], 2)
        self.assertEqual(result[0]['count'], 1)
        self.assertIn('Needle', result[0]['excerpt'])
        self.assertNotIn('html', result[0])
        for query in ['', '.*', '<script>']:
            self.assertEqual(client.get(url, query_string={'q': query}).json, {'results': []})
        self.assertEqual(client.get(url, query_string={'q': 'x'*201}).status_code, 400)

    def test_disallowed_custom_builtin_and_other_assessment_are_denied(self):
        client = self.client(self.load())
        for path in ['demo/references/private', 'demo/references/java_reference', 'missing/references/notes']:
            self.assertEqual(client.get('/api/assessment/'+path).status_code, 404)

    def test_fenced_code_is_not_split_at_heading_like_text(self):
        source = '# Heading\n\n## Code\n\n```python\n## not a section\n```\n\n## End\n\nDone'
        sections = split_sections(source)
        self.assertEqual([s['title'] for s in sections], ['Overview', 'Code', 'End'])
        self.assertIn('## not a section', sections[1]['source'])


if __name__ == '__main__':
    unittest.main()
