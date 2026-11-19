import json
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile
from club.assessments import AssessmentParser
from club.grading import grade_response
from club.interactive import diagnostics


class AssessmentFormatTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.folder = self.root / 'demo'; self.folder.mkdir()
        self.text = 'Quotes " \\frac{x_i}{2}\r\n$y$\n'
        (self.folder/'arbitrary.asset').write_bytes(self.text.encode())
        self.manifest = {'id':'demo','title':'Demo','stimuli':{'body':{'$file':'arbitrary.asset'}},'questions':[{'id':'q','response_type':'code_editor','response_config':{'supported_languages':['python'],'default_code':{'python':{'$file':'arbitrary.asset'}},'grader':{'code':'def grade(ctx): ctx.award(3)','max_score':5}}}]}
        (self.folder/'assessment.json').write_text(json.dumps(self.manifest))
        self.parser = AssessmentParser(self.root)

    def test_folder_json_and_zip_preserve_exact_text(self):
        with ZipFile(self.root/'demo.zip','w') as archive:
            for p in self.folder.iterdir():archive.write(p,'wrapper/'+p.name)
        for name in ['demo','demo/assessment.json','demo.zip']:
            item=self.parser.load(name)
            self.assertEqual(item['stimuli']['body'], self.text)
            c=item['questions'][0]['response_config']
            self.assertEqual(c['default_code']['python'], self.text)
            self.assertFalse(c['file_browser']);self.assertFalse(c['read_only'])

    def test_escape_paths_rejected(self):
        self.manifest['stimuli']['body']={'$file':'../secret'}
        (self.folder/'assessment.json').write_text(json.dumps(self.manifest))
        with self.assertRaises(ValueError):self.parser.load('demo')
        with ZipFile(self.root/'bad.zip','w') as archive:
            archive.writestr('../assessment.json',json.dumps(self.manifest))
        with self.assertRaises(ValueError):self.parser.load('bad.zip')

    def test_tryout_structure(self):
        from club.config import BASE_DIR
        item=AssessmentParser(BASE_DIR/'private_assessments').load('tryout_test')
        self.assertEqual([q['id'] for q in item['questions']],['student','instructions','odd_ones_out','swapped_spelling','academic_comeback'])
        self.assertEqual(len(item['questions'][0]['response_config']['fields']),3)
        root=BASE_DIR/'private_assessments'/'tryout_test'
        self.assertEqual(len(list((root/'tests').glob('*.py'))),3)
        self.assertEqual(len(list((root/'tests').glob('*.txt'))),3)
        self.assertEqual(sum(q['response_config']['score_max'] for q in item['questions']),300)

    def test_private_grader_defaults_removed(self):
        from club.routes import public_assessment
        item=self.parser.load('demo')
        item['response_defaults']={'code_editor':{'grader':{'code':'SECRET'}}}
        public=public_assessment(item)
        self.assertNotIn('response_defaults',public)
        self.assertNotIn('grader',public['questions'][0]['response_config'])


class GraderTests(unittest.TestCase):
    def test_custom_points_override_and_case_names(self):
        grader={'code':'def grade(ctx):\n ctx.check("", "42", points=7, large=True)\n ctx.set_assessment_score(70, 100)\n','max_score':10}
        result=grade_response('python','print(42)',grader,{})
        self.assertEqual(result['earned'],7)
        self.assertEqual(result['tests'][0]['name'],'Test 1 (Large Input)')
        self.assertEqual(result['assessment_score'],{'earned':70,'maximum':100})

    def test_timeout_output_and_memory_limits(self):
        for code,limit,expected in [('while True: pass','timeout=.08','Time limit exceeded'),('print("x" * 100000)','output_limit=100','Output limit exceeded'),('import time\nx=bytearray(100000000)\ntime.sleep(2)','memory_mb=32','Memory limit exceeded')]:
            with self.subTest(expected=expected):
                grader={'code':f'def grade(ctx):\n ctx.check("", "", {limit})','max_score':1}
                result=grade_response('python',code,grader,{})
                self.assertEqual(result['earned'],0)
                self.assertEqual(result['tests'][0]['output'],expected)

    def test_python_ranges_and_undefined_name(self):
        markers=diagnostics('python','print(missing_name)')
        marker=next(m for m in markers if 'missing_name' in m['message'])
        self.assertEqual(marker['column'],7)
        self.assertEqual(marker['end_column'],19)


class ScoringHookTests(unittest.TestCase):
    def test_short_answer_grader_and_required_fields(self):
        from club import create_app
        from unittest.mock import patch
        from club.config import BASE_DIR
        with tempfile.TemporaryDirectory() as directory:
            app=create_app({'TESTING':True,'ATTEMPT_DATABASE':Path(directory)/'test.sqlite3'})
            client=app.test_client()
            item={'id':'short','title':'Short','questions':[{'id':'student','response_type':'short_answer','response_config':{'fields':[{'id':'name','question_text':'Name','required':True,'character_limit':100}], 'grader':{'code':'def grade(ctx): ctx.set_score(7, maximum=10)','max_score':10}}}], 'time_limit_seconds':0,'number_of_attempts':0,'passcode':'','submittable_early':True}
            with patch('club.routes.parser.load_all',return_value=[item]):
                attempt=client.post('/api/assessment/short/attempt',json={}).json['attempt']
                url='/api/attempt/'+attempt['id']
                self.assertEqual(client.post(url,json={'answers':{},'submit':True}).status_code,400)
                response=client.post(url,json={'answers':{'student:name':'Sample'},'submit':True})
                self.assertEqual(response.status_code,200)
                self.assertEqual(response.json['attempt']['score']['student']['earned'],7)

    def test_prompts_do_not_affect_stdout_grading(self):
        result=grade_response('python', 'import sys\nprint("Enter a number: ", file=sys.stderr, end="", flush=True)\nprint(int(input())*2)', {'code':'def grade(ctx): ctx.check("21\\n", "42")','max_score':1}, {})
        self.assertEqual(result['earned'],1)

if __name__=='__main__':unittest.main()
