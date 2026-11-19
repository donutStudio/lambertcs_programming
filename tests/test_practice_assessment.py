"""Validate the installed bundle through the real parser, graders, and routes."""
import json
import tempfile
import unittest
from pathlib import Path

from club import create_app
from club.assessments import AssessmentParser
from club.config import BASE_DIR
from club.grading import grade_response


# These implementations are only test fixtures; they are never served to students.
# They are inserted into the provided starters so input/output wiring is tested too.
SOLUTIONS = {
    'candle_split': '''    if n % 2:
        return 'NO'
    return 'YES' if n - 2 > 2 else 'NO'
''',
    'digit_difference': '''    digits = []
    while n:
        digits.append(n % 10)
        n //= 10
    return max(digits) - min(digits)
''',
    'vowel_check': '''    count = 0
    for letter in word:
        if letter in 'aeiou':
            count += 1
    return count
''',
    'next_squares': '''    root = 1
    while root * root < k:
        root += 1
    return (root + n - 1) ** 2
''',
    'club_initials': '''    result = ''
    for i, letter in enumerate(name):
        if i == 0 or name[i - 1] == ' ':
            result += letter
    return result
''',
    'seat_shift': '''    size = len(seats)
    return ' '.join(str(seats[(i - shift) % size]) for i in range(size))
''',
    'practice_streak': '''    best = current = 0
    for day in days:
        current = current + 1 if day else 0
        best = max(best, current)
    return best
''',
    'snack_vote': '''    counts = [0] * 26
    for letter in votes:
        counts[ord(letter) - ord('a')] += 1
    return chr(ord('a') + counts.index(max(counts)))
''',
    'merged_line': '''    merged = []
    i = j = 0
    while i < len(first) and j < len(second):
        if first[i] <= second[j]:
            merged.append(first[i])
            i += 1
        else:
            merged.append(second[j])
            j += 1
    merged.extend(first[i:])
    merged.extend(second[j:])
    return ' '.join(map(str, merged))
''',
    'reading_goal': '''    left = total = 0
    best = len(pages) + 1
    for right, count in enumerate(pages):
        total += count
        while total >= goal:
            best = min(best, right - left + 1)
            total -= pages[left]
            left += 1
    return best if best <= len(pages) else -1
''',
}


class PracticeAssessmentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.item = AssessmentParser().load('practice_programming')

    def test_only_practice_is_installed_with_unlimited_untimed_access(self):
        self.assertEqual([a['id'] for a in AssessmentParser().load_all()], ['practice_programming'])
        self.assertFalse((BASE_DIR/'assessments/tryout_test').exists())
        for setting, value in [('time_limit_seconds', 0), ('number_of_attempts', 0), ('passcode', '')]:
            self.assertEqual(self.item[setting], value)
        questions = self.item['questions']
        self.assertEqual([q['id'] for q in questions[:2]], ['student', 'instructions'])
        self.assertEqual([q['id'] for q in questions[2:]], list(SOLUTIONS))
        self.assertEqual(sum(q['response_config']['score_max'] for q in questions), 1000)

    def test_reference_solutions_pass_all_cases_using_provided_starters(self):
        for q in self.item['questions'][2:]:
            with self.subTest(problem=q['id']):
                config = q['response_config']
                self.assertEqual(config['supported_languages'], ['python', 'java', 'cpp'])
                self.assertEqual(set(config['default_code']), {'python', 'java', 'cpp'})
                cases = json.loads(config['grader']['assets']['cases'])
                self.assertEqual(len(cases), 10)
                self.assertTrue(any(c['hidden'] for c in cases))
                text = self.item['stimuli'][q['id']].replace('\r\n', '\n')
                self.assertIn('**Input Format**\n<br>', text)
                self.assertIn('|#|**Sample Input**|**Sample Output**|', text)
                self.assertIn('Constraints:\n<br>', text)
                self.assertIn('**Sample Explanations**', text)
                for c in cases:
                    if not c['hidden']:
                        sample = '<br>'.join('`'+line+'`' for line in c['input'].strip().splitlines())
                        self.assertIn(sample+'|`'+c['expected']+'`|', text)
                code = config['default_code']['python'].replace('\r\n', '\n').replace('    # Your code here!\n    pass\n', SOLUTIONS[q['id']])
                result = grade_response('python', code, config['grader'], {})
                self.assertEqual(result['earned'], 100, result['tests'])

    def test_tryout_routes_unavailable_and_repeat_attempts_allowed(self):
        with tempfile.TemporaryDirectory() as directory:
            app = create_app({'TESTING': True, 'SECRET_KEY': 'practice-tests',
                              'ATTEMPT_DATABASE': Path(directory)/'attempts.sqlite3'})
            client = app.test_client()
            self.assertEqual(client.get('/assessment/tryout_test').status_code, 404)
            self.assertEqual(client.post('/api/assessment/tryout_test/attempt', json={}).status_code, 404)
            self.assertEqual(client.get('/assessment/practice_programming').status_code, 200)
            self.assertEqual(set(client.get('/api/assignments').json), {'practice_programming'})
            for _ in range(3):
                response = client.post('/api/assessment/practice_programming/attempt', json={})
                self.assertEqual(response.status_code, 200)
                attempt = response.json['attempt']
                self.assertIsNone(attempt['deadline'])
                response = client.post('/api/attempt/'+attempt['id'], json={
                    'submit': True, 'answers': {'student:full_name': 'Practice Student',
                        'student:email': 'practice@example.com', 'student:student_id': '123'}})
                self.assertEqual(response.status_code, 200)


if __name__ == '__main__':
    unittest.main()
