"""Bounded local interactive processes and non-executing editor diagnostics."""
import ast
import builtins
import symtable
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


def prepare(language, code, directory, compile_timeout=20):
    root = Path(directory)
    source = root / {"python": "main.py", "java": "Main.java", "cpp": "main.cpp"}[language]
    source.write_text(code, encoding="utf-8")
    if language == "python":
        return [sys.executable, "-I", "-u", str(source)], ""
    command = ["javac", "Main.java"] if language == "java" else ["g++", "-std=c++17", "main.cpp", "-o", "main"]
    result = execute(command, root, timeout=compile_timeout)
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
            if self.process:
                if self.process.stdin and not self.process.stdin.closed: self.process.stdin.close()
                if self.process.stdout: self.process.stdout.close()
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
                            markers.append({"line": node.lineno, "column": node.col_offset + 1, "end_line": node.end_lineno, "end_column": node.end_col_offset + 1, "severity": "warning", "message": f"Imported '{name}' is not used."})
            table = symtable.symtable(code, "main.py", "exec")
            known = set(dir(builtins)) | {"__name__", "__file__", "__doc__", "__package__", "__builtins__"}
            known |= {symbol.get_name() for symbol in table.get_symbols() if symbol.is_assigned() or symbol.is_imported() or symbol.is_namespace()}
            def check_scope(scope):
                unknown = {symbol.get_name() for symbol in scope.get_symbols() if symbol.is_referenced() and symbol.is_global() and symbol.get_name() not in known}
                for node in ast.walk(tree):
                    if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load) and node.id in unknown and scope.get_lineno() <= node.lineno:
                        marker = {"line": node.lineno, "column": node.col_offset + 1, "end_line": node.end_lineno, "end_column": node.end_col_offset + 1, "severity": "warning", "message": f"Name '{node.id}' may be undefined."}
                        if marker not in markers: markers.append(marker)
                for child in scope.get_children(): check_scope(child)
            check_scope(table)
        except SyntaxError as error:
            markers.append({"line": error.lineno or 1, "column": error.offset or 1,
                            "end_line": error.end_lineno or error.lineno or 1,
                            "end_column": max((error.offset or 1) + 1, error.end_offset or 1),
                            "severity": "error", "message": error.msg})
        return markers
    with TemporaryDirectory() as directory:
        filename = "Main.java" if language == "java" else "main.cpp"
        (Path(directory) / filename).write_text(code, encoding="utf-8")
        command = ["javac", "-Xlint:all", filename] if language == "java" else ["g++", "-std=c++17", "-Wall", "-Wextra", "-fsyntax-only", filename]
        try:
            result = execute(command, directory, timeout=15)
        except FileNotFoundError:
            return [{"line": 1, "column": 1, "severity": "info", "message": "Diagnostics unavailable: compiler is not installed."}]
        diagnostic_lines = result.stderr.splitlines()
        for index, line in enumerate(diagnostic_lines):
            match = re.search(r'(?:Main\.java|main\.cpp):(\d+):(?:(\d+):)?\s*(error|warning):\s*(.*)', line)
            if match:
                number = int(match[1])
                column = int(match[2] or 1)
                for following in diagnostic_lines[index+1:index+4]:
                    if "^" in following:
                        caret = following.split("|",1)[-1] if "|" in following else following
                        if match[2] is None: column = caret.index("^") + 1
                        break
                source_line = code.splitlines()[number-1] if number <= len(code.splitlines()) else ""
                token = re.match(r"[A-Za-z_][A-Za-z_0-9]*", source_line[max(0,column-1):])
                end = column + (len(token[0]) if token else 1)
                markers.append({"line": number, "column": column, "end_line": number, "end_column": end, "severity": match[3], "message": match[4]})
    return markers[:100]
