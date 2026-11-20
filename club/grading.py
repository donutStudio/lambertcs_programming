"""Trusted assessment-authored Python graders. Never execute client-supplied graders.

A grader defines grade(ctx). ctx.run() compiles the student's source once, then
runs it with explicit runtime/memory/output limits. ctx.award()/set_score() own
this response's score; ctx.set_assessment_score() can override the total.
"""
import math
import sys
from pathlib import Path
import subprocess
import threading
import time
from tempfile import TemporaryDirectory
from types import SimpleNamespace

import psutil

from .interactive import prepare


class GradeContext:
    def __init__(self, language, code, grader, answers):
        self.language, self.code = language, code
        self.assets = grader.get('assets', {})
        self.answers = answers
        self.score = 0
        self.maximum = grader.get('max_score', 0)
        self.tests = []
        self.assessment_score = None
        self.temp = TemporaryDirectory()
        self.command = None
        self.prepared = False
        self.compile_error = ""

    def set_score(self, score, maximum=None):
        if not math.isfinite(float(score)):
            raise ValueError('Score must be finite')
        self.score = float(score)
        if maximum is not None:
            self.maximum = float(maximum)

    def award(self, points):
        self.set_score(self.score + points)

    def set_assessment_score(self, score, maximum):
        if not all(math.isfinite(float(v)) for v in (score, maximum)) or maximum < 0:
            raise ValueError('Invalid assessment score')
        self.assessment_score = {'earned': score, 'maximum': maximum}

    def run(self, input='', *, timeout=2, memory_mb=256, output_limit=100000, compile_timeout=30):
        if not self.prepared:
            self.command, self.compile_error = prepare(self.language, self.code, self.temp.name, compile_timeout=compile_timeout)
            if self.language == 'python':
                # input(prompt) is UI, not an answer. Keep prompts visible in the
                # interactive terminal, but suppress them during automated grading.
                runner = Path(self.temp.name) / '_grade_runner.py'
                runner.write_text('import builtins, runpy\n'
                                  '_input = builtins.input\n'
                                  'def quiet_input(prompt=""):\n    return _input()\n'
                                  'builtins.input = quiet_input\n'
                                  'runpy.run_path("main.py", run_name="__main__")\n', encoding='utf-8')
                self.command = [sys.executable, '-I', '-u', str(runner)]
            self.prepared = True
        if self.compile_error:
            return SimpleNamespace(output="", stderr=self.compile_error, returncode=1, timed_out=False, memory_exceeded=False, output_exceeded=False, elapsed=0)
        started = time.monotonic()
        process = subprocess.Popen(self.command, cwd=self.temp.name, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        output = bytearray()
        stderr = bytearray()
        output_lock = threading.Lock()
        flags = {'timed_out': False, 'memory_exceeded': False, 'output_exceeded': False}
        def kill():
            try:
                parent = psutil.Process(process.pid)
                for child in parent.children(recursive=True):
                    try: child.kill()
                    except psutil.Error: pass
                parent.kill()
            except psutil.Error: pass
        def read_output(stream, buffer):
            while True:
                chunk = stream.read(4096)
                if not chunk: break
                with output_lock:
                    room = max(0, output_limit - len(output) - len(stderr))
                    buffer.extend(chunk[:room])
                if len(chunk) > room:
                    flags['output_exceeded'] = True
                    kill()
        def write_input():
            try:
                process.stdin.write(input.encode())
                process.stdin.close()
            except (BrokenPipeError, OSError): pass
        reader = threading.Thread(target=read_output, args=(process.stdout, output), daemon=True)
        error_reader = threading.Thread(target=read_output, args=(process.stderr, stderr), daemon=True)
        writer = threading.Thread(target=write_input, daemon=True)
        reader.start(); error_reader.start(); writer.start()
        while process.poll() is None:
            if time.monotonic() - started > timeout:
                flags['timed_out'] = True
                kill()
            try:
                parent = psutil.Process(process.pid)
                usage = parent.memory_info().rss + sum(p.memory_info().rss for p in parent.children(recursive=True))
                if usage > memory_mb * 1024 * 1024:
                    flags['memory_exceeded'] = True
                    kill()
            except psutil.Error: pass
            time.sleep(.01)
        process.wait()
        reader.join(timeout=1); error_reader.join(timeout=1); writer.join(timeout=1)
        process.stdout.close()
        process.stderr.close()
        if not process.stdin.closed: process.stdin.close()
        return SimpleNamespace(output=output.decode('utf-8', errors='replace'), stderr=stderr.decode('utf-8', errors='replace'), returncode=process.returncode,
                               elapsed=time.monotonic() - started, **flags)

    def check(self, input, expected, *, points=1, large=False, hidden=False, **limits):
        result = self.run(input, **limits)
        passed = result.returncode == 0 and not any((result.timed_out, result.memory_exceeded, result.output_exceeded)) and result.output.rstrip() == expected.rstrip()
        if passed: self.award(points)
        message = 'Passed' if passed else 'Time limit exceeded' if result.timed_out else 'Memory limit exceeded' if result.memory_exceeded else 'Output limit exceeded' if result.output_exceeded else 'Hidden test failed' if hidden else result.output or result.stderr or 'Incorrect output'
        self.tests.append({'name': f'Test {len(self.tests)+1}' + (' (Large Input)' if large else ''),
                           'passed': passed, 'output': message, 'hidden': hidden})
        return result


def grade_response(language, code, grader, answers):
    context = GradeContext(language, code, grader, answers)
    try:
        namespace = {'__name__': 'assessment_grader'}
        exec(compile(grader['code'], '<assessment grader>', 'exec'), namespace)
        namespace['grade'](context)
        if not math.isfinite(float(context.maximum)) or context.maximum < 0:
            raise ValueError('Invalid maximum score')
        return {'earned': context.score, 'maximum': context.maximum, 'tests': context.tests,
                'assessment_score': context.assessment_score}
    finally:
        context.temp.cleanup()
