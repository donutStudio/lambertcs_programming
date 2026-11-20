"""Regression checks for the Friday tryout definitions and trusted graders."""
import itertools
import json
import unittest
from club.assessments import AssessmentParser
from club.grading import grade_response


class TryoutBTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.item = AssessmentParser().load('tryout_test_b')

    def test_all_listed_bundles_load(self):
        items = AssessmentParser().load_all()
        self.assertEqual(len({item["id"] for item in items}), len(items))

    def test_layout_and_starters(self):
        self.assertEqual([q['id'] for q in self.item['questions']],
                         ['instructions', 'fizzes_and_buzzes', 'splling', 'dropping_grades'])
        for question in self.item['questions'][1:]:
            config = question['response_config']
            self.assertEqual(set(config['default_code']), {'python', 'java', 'cpp'})
            cases = json.loads(config['grader']['assets']['cases'])
            self.assertEqual(len(cases), 10)
            self.assertTrue(any(c['large'] for c in cases))

    def test_case_answers_with_independent_oracles(self):
        for question in self.item['questions'][1:]:
            for case in json.loads(question['response_config']['grader']['assets']['cases']):
                if question['id'] == 'fizzes_and_buzzes':
                    n = int(case['input'])
                    expected = sum(i for i in range(n+1) if (i % 3 == 0) != (i % 5 == 0))
                elif question['id'] == 'splling':
                    a, b = case['input'].splitlines()
                    # Remove one internal e from the target and compare exactly.
                    if len(a) < 1000:
                        possible = a == b or any(b[i] == 'e' and b[:i]+b[i+1:] == a for i in range(1,len(b)-1))
                    else:
                        # Large fixtures contain exactly one e, avoiding quadratic slicing.
                        i = b.index('e')
                        possible = 0 < i < len(b)-1 and b[:i]+b[i+1:] == a
                    expected = 'Yes!' if possible else 'No!'
                else:
                    grades = list(map(int, case['input'].split()))
                    if len(grades) < 20:
                        expected = next((k for k in range(min(3,len(grades)-1)+1)
                                         if any(sum(grades)-sum(drop) >= 90*(len(grades)-k)
                                                for drop in itertools.combinations(grades,k))), -1)
                    else:
                        counts = [0]*101
                        for grade in grades: counts[grade] += 1
                        total, remaining, expected = sum(grades), len(grades), -1
                        for k in range(4):
                            if total >= 90*remaining:
                                expected = k; break
                            lowest = next(i for i,c in enumerate(counts) if c)
                            counts[lowest] -= 1; total -= lowest; remaining -= 1
                self.assertEqual(str(expected), case['expected'], question['id'])

    def test_graders_accept_correct_programs(self):
        programs = {
            'fizzes_and_buzzes': 'n=int(input()); print(sum(i for i in range(n+1) if (i%3==0)!=(i%5==0)))',
            'splling': "a=input(); b=input(); i=0\nwhile i<len(a) and i<len(b) and a[i]==b[i]: i+=1\nok=a==b\nif len(b)==len(a)+1:\n for j in range(max(1,i-1),min(len(a),i+1)):\n  ok |= b[j]=='e' and a[:j]==b[:j] and a[j:]==b[j+1:]\nprint('Yes!' if ok else 'No!')",
            'dropping_grades': 'g=sorted(map(int,input().split())); total=sum(g); answer=-1\nfor k in range(min(3,len(g)-1)+1):\n if total>=90*(len(g)-k): answer=k; break\n total-=g[k]\nprint(answer)',
        }
        for question in self.item['questions'][1:]:
            result = grade_response('python', programs[question['id']], question['response_config']['grader'], {})
            self.assertEqual(result['earned'], 100, question['id'])
            self.assertTrue(all(test['passed'] for test in result['tests']))
