"""Page routes and the code execution endpoint."""
import subprocess

from flask import Blueprint, current_app, jsonify, render_template, request, url_for

from .config import MAX_CODE_LENGTH, MONACO_BASE
from .execution import run_code
from .languages import LANGUAGES
from .problems import load_problem

pages = Blueprint("pages", __name__)


@pages.get("/")
def index():
    return render_template("index.html")


@pages.get("/editor")
def editor():
    return render_template(
        "editor.html",
        problem_html=load_problem(),
        languages=LANGUAGES,
        editor_config={
            "languages": LANGUAGES,
            "initialLanguage": "python",
            "monacoBase": MONACO_BASE,
            "runUrl": url_for("pages.run"),
        },
        monaco_base=MONACO_BASE,
    )


@pages.route("/run", methods=["POST"])
def run():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"output": "Invalid request!"}), 400

    language = data.get("language")
    code = data.get("code")

    if not isinstance(language, str) or language not in LANGUAGES:
        return jsonify({"output": "Unsupported language."}), 400

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
        current_app.logger.exception("Code execution failed")
        output = "An internal execution error occurred!"

    return jsonify({"output": output})


