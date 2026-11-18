"""Compile and execute submitted programs on the local machine."""
from pathlib import Path
from tempfile import TemporaryDirectory
import subprocess
import sys

from .config import MAX_OUTPUT_LENGTH, TIMEOUT


def execute(command, cwd):
    return subprocess.run(
        command,
        cwd=cwd,
        capture_output=True,
        text=True,
        errors="replace",
        timeout=TIMEOUT,
        stdin=subprocess.DEVNULL
    )


def run_code(language, code):
    with TemporaryDirectory() as temp_dir:
        workdir = Path(temp_dir)

        if language == "python":
            source = workdir / "main.py"
            source.write_text(code, encoding="utf-8")

            result = execute(
                [sys.executable, "-I", str(source)],
                workdir
            )

        elif language == "java":
            source = workdir / "Main.java"
            source.write_text(code, encoding="utf-8")

            compile_result = execute(
                ["javac", "Main.java"],
                workdir
            )

            if compile_result.returncode != 0:
                return (compile_result.stdout + compile_result.stderr)[:MAX_OUTPUT_LENGTH]

            result = execute(
                ["java", "-cp", str(workdir), "Main"],
                workdir
            )

        elif language == "cpp":
            source = workdir / "main.cpp"
            source.write_text(code, encoding="utf-8")

            compile_result = execute(
                ["g++", "-std=c++17", "main.cpp", "-o", "main"],
                workdir
            )

            if compile_result.returncode != 0:
                return (compile_result.stdout + compile_result.stderr)[:MAX_OUTPUT_LENGTH]

            result = execute(
                [str(workdir / ("main.exe" if sys.platform == "win32" else "main"))],
                workdir
            )

        else:
            return "Unsupported language."

        output = result.stdout + result.stderr

        if not output:
            if result.returncode == 0:
                return ""
            return f"Program exited with code {result.returncode}."

        return output[:MAX_OUTPUT_LENGTH]


