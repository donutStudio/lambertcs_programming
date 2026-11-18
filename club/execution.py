"""Compile and execute submitted programs on the local machine."""
from pathlib import Path
from tempfile import TemporaryDirectory
import subprocess
import sys

from .config import MAX_OUTPUT_LENGTH, TIMEOUT


def execute(command, cwd, input_text="", timeout=TIMEOUT):

    return subprocess.run(
        command,
        cwd=cwd,
        capture_output=True,
        text=True,
        errors="replace",
        timeout=timeout,
        input=input_text
    )


def run_code(language, code, input_text=""):

    with TemporaryDirectory() as temp_dir:
        workdir = Path(temp_dir)

        if language == "python":
            source = workdir / "main.py"
            source.write_text(code, encoding="utf-8")

            result = execute(
                [sys.executable, "-I", str(source)],
                workdir, input_text
            )

        elif language == "java":
            source = workdir / "Main.java"
            source.write_text(code, encoding="utf-8")

            compile_result = execute(
                ["javac", "Main.java"],
                workdir, timeout=20
            )

            if compile_result.returncode != 0:
                return format_result(compile_result, "compile")

            result = execute(
                ["java", "-cp", str(workdir), "Main"],
                workdir, input_text
            )

        elif language == "cpp":
            source = workdir / "main.cpp"
            source.write_text(code, encoding="utf-8")

            compile_result = execute(
                ["g++", "-std=c++17", "main.cpp", "-o", "main"],
                workdir, timeout=20
            )

            if compile_result.returncode != 0:
                return format_result(compile_result, "compile")

            result = execute(
                [str(workdir / ("main.exe" if sys.platform == "win32" else "main"))],
                workdir, input_text
            )

        else:
            return "Unsupported language."

        return format_result(result, "run")




def format_result(result, stage):
    """Return program output, adding a summary only when the process failed."""
    output = result.stdout + result.stderr
    if result.returncode == 0:
        if not output:
            output = "(no output)"
    else:
        output = output.rstrip() + f"\n\n{stage.capitalize()} finished with exit code {result.returncode}."
    return output[:MAX_OUTPUT_LENGTH]
