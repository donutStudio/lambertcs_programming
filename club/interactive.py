"""Bounded local interactive processes and non-executing editor diagnostics."""
import ast
import os
import re
import secrets
import subprocess
import sys
import threading
import time
from pathlib import Path
from tempfile import TemporaryDirectory

from .config import MAX_OUTPUT_LENGTH
from .execution import execute

SESSIONS = {}
LOCK = threading.Lock()


def prepare(language, code, directory):
    root = Path(directory)
    source = root / {"python": "main.py", "java": "Main.java", "cpp": "main.cpp"}[language]
    source.write_text(code, encoding="utf-8")
    if language == "python":
        return [sys.executable, "-I", "-u", str(source)], ""
    command = ["javac", "Main.java"] if language == "java" else ["g++", "-std=c++17", "main.cpp", "-o", "main"]
    result = execute(command, root, timeout=20)
    if result.returncode:
        return None, (result.stdout + result.stderr)[:MAX_OUTPUT_LENGTH]
    return (["java", "-cp", str(root), "Main"] if language == "java" else [str(root / ("main.exe" if sys.platform == "win32" else "main"))]), ""


class RunningProgram:
    def __init__(self, owner, language, code):
        self.owner = owner
        self.temp = TemporaryDirectory()
        self.output = ""
        self.done = False
        self.process = None
        self.lock = threading.Lock()
        self.started = time.monotonic()
        self.language, self.code = language, code
        threading.Thread(target=self.run, daemon=True).start()

    def append(self, value):
        with self.lock:
            room = MAX_OUTPUT_LENGTH - len(self.output)
            self.output += value[:room]
        if room <= len(value) and self.process and self.process.poll() is None:
            self.process.kill()

    def run(self):
        timer = threading.Timer(120, self.stop)
        timer.daemon = True
        timer.start()
        try:
            command, error = prepare(self.language, self.code, self.temp.name)
            if error:
                self.append(error)
                return
            self.process = subprocess.Popen(command, cwd=self.temp.name, stdin=subprocess.PIPE,
                                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                            text=True, encoding="utf-8", errors="replace", bufsize=0,
                                            env={**os.environ, "PYTHONIOENCODING": "utf-8"})
            if time.monotonic() - self.started >= 120:
                self.stop()
            while True:
                char = self.process.stdout.read(1)
                if not char:
                    break
                self.append(char)
            code = self.process.wait()
            self.append(f"\n[Process exited {code}]\n")
        except Exception as error:
            self.append(f"\n{type(error).__name__}: {error}\n")
        finally:
            timer.cancel()
            self.done = True
            self.temp.cleanup()

    def stop(self):
        if self.process and self.process.poll() is None:
            self.process.kill()


def start_program(owner, language, code):
    with LOCK:
        for key, process in list(SESSIONS.items()):
            if process.done and time.monotonic() - process.started > 180:
                del SESSIONS[key]
        if sum(not p.done for p in SESSIONS.values()) >= 32 or sum(not p.done and p.owner == owner for p in SESSIONS.values()) >= 2:
            raise ValueError("Stop an existing program before starting another.")
        key = secrets.token_hex(24)
        SESSIONS[key] = RunningProgram(owner, language, code)
        return key


def diagnostics(language, code):
    markers = []
    if language == "python":
        try:
            tree = ast.parse(code)
            compile(tree, "main.py", "exec")
            used = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)}
            for node in ast.walk(tree):
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    for alias in node.names:
                        name = alias.asname or alias.name.split(".")[0]
                        if name != "*" and name not in used:
                            markers.append({"line": node.lineno, "column": node.col_offset + 1, "severity": "warning", "message": f"Imported '{name}' is not used."})
        except SyntaxError as error:
            markers.append({"line": error.lineno or 1, "column": error.offset or 1, "severity": "error", "message": error.msg})
        return markers
    with TemporaryDirectory() as directory:
        filename = "Main.java" if language == "java" else "main.cpp"
        (Path(directory) / filename).write_text(code, encoding="utf-8")
        command = ["javac", "-Xlint:all", filename] if language == "java" else ["g++", "-std=c++17", "-Wall", "-Wextra", "-fsyntax-only", filename]
        try:
            result = execute(command, directory, timeout=15)
        except FileNotFoundError:
            return [{"line": 1, "column": 1, "severity": "info", "message": "Diagnostics unavailable: compiler is not installed."}]
        for line in result.stderr.splitlines():
            match = re.search(r'(?:Main\.java|main\.cpp):(\d+):(?:(\d+):)?\s*(error|warning):\s*(.*)', line)
            if match:
                markers.append({"line": int(match[1]), "column": int(match[2] or 1), "severity": match[3], "message": match[4]})
    return markers[:100]
