
from pathlib import Path
from tempfile import TemporaryDirectory
import subprocess
import sys

import markdown
from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

BASE_DIR = Path(__file__).resolve().parent

PROBLEM_FILE = BASE_DIR / "problems" / "example" / "next_squares.md"

TIMEOUT = 5
MAX_CODE_LENGTH = 20000
MAX_OUTPUT_LENGTH = 10000


@app.route("/")
def index():
    content = PROBLEM_FILE.read_text(encoding="utf-8")

    problem_html = markdown.markdown(
        content,
        extensions=["fenced_code", "tables"]
    )

    return render_template(
        "index.html",
        problem_html=problem_html
    )


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
                return (
                    compile_result.stdout
                    + compile_result.stderr
                )

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
                return (
                    compile_result.stdout
                    + compile_result.stderr
                )

            result = execute(
                [str(workdir / "main")],
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


@app.route("/run", methods=["POST"])
def run():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"output": "Invalid request!"}), 400

    language = data.get("language")
    code = data.get("code")

    if not isinstance(code, str):
        return jsonify({"output": "Invalid code!"}), 400

    if len(code) > MAX_CODE_LENGTH:
        return jsonify({"output": "Code is too long!"}), 400

    try:
        output = run_code(language, code)

    except subprocess.TimeoutExpired:
        output = "Code execution timed out!"

    except FileNotFoundError as error:
        output = (
            f"Could not run executable: {error.filename}\n"
            "Correct compiler/interpreter not installed on the machine!"
        )

    except Exception:
        app.logger.exception("Code execution failed")
        output = "An internal execution error occured!"

    return jsonify({"output": output})


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
