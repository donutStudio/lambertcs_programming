"""Assessment pages, submissions, and the local code runner."""
import csv
import io
import json
import subprocess
from datetime import datetime, timezone

from flask import Blueprint, current_app, jsonify, make_response, render_template, request, url_for

from .assessments import AssessmentAttempt, AssessmentParser
from .config import BASE_DIR, MAX_CODE_LENGTH, MONACO_BASE
from .execution import run_code
from .languages import LANGUAGES
from .problems import load_problem, markdown

pages = Blueprint("pages", __name__)
parser = AssessmentParser()


def find_assessment(assessment_id):
    return next((item for item in parser.load_all() if item["id"] == assessment_id), None)


@pages.get("/")
def index():
    return render_template("index.html", assessments=parser.load_all())


@pages.get("/assessment/<assessment_id>")
def assessment(assessment_id):
    item = find_assessment(assessment_id)
    if item is None:
        return "Assessment not found", 404
    AssessmentAttempt(item)
    config = {
        "assessment": item,
        "languages": LANGUAGES,
        "monacoBase": MONACO_BASE,
        "runUrl": url_for("pages.run"),
        "testsUrl": url_for("pages.run_tests", assessment_id=assessment_id),
        "submitUrl": url_for("pages.submit", assessment_id=assessment_id),
        "stimuliHtml": {key: markdown.markdown(value, extensions=["fenced_code", "tables"])
                        for key, value in item.get("stimuli", {}).items()},
    }
    for question in item["questions"]:
        for field in question.get("response_config", {}).get("fields", []):
            field["question_html"] = markdown.markdown(field.get("question_text", ""))
    return render_template("assessment.html", assessment=item, config=config, monaco_base=MONACO_BASE)


@pages.post("/assessment/<assessment_id>/submit")
def submit(assessment_id):
    item = find_assessment(assessment_id)
    if item is None:
        return jsonify({"error": "Assessment not found"}), 404
    data = request.get_json(silent=True) or {}
    submissions = BASE_DIR / "submissions"
    submissions.mkdir(exist_ok=True)
    submitted_at = datetime.now(timezone.utc).isoformat()
    record = {"assessment_id": assessment_id, "assessment_title": item["title"],
              "submitted_at": submitted_at, "answers": data.get("answers", {}),
              "score": data.get("score", {})}
    path = submissions / f"{assessment_id}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.json"
    path.write_text(json.dumps(record, indent=2), encoding="utf-8")
    return jsonify({"saved": True, "submitted_at": submitted_at})


@pages.get("/export/submissions.csv")
def export_submissions():
    stream = io.StringIO()
    writer = csv.writer(stream)
    writer.writerow(["assessment_id", "assessment_title", "submitted_at", "score", "answers"])
    for path in sorted((BASE_DIR / "submissions").glob("*.json")):
        item = json.loads(path.read_text(encoding="utf-8"))
        writer.writerow([item.get("assessment_id"), item.get("assessment_title"),
                         item.get("submitted_at"), json.dumps(item.get("score", {})),
                         json.dumps(item.get("answers", {}))])
    response = make_response(stream.getvalue())
    response.headers["Content-Type"] = "text/csv; charset=utf-8"
    response.headers["Content-Disposition"] = "attachment; filename=submissions.csv"
    return response


def validate_run_request(data):
    if not isinstance(data, dict):
        return None, None, ("Invalid request!", 400)
    language, code = data.get("language"), data.get("code")
    if not isinstance(language, str) or language not in LANGUAGES:
        return None, None, ("Unsupported language.", 400)
    if not isinstance(code, str):
        return None, None, ("Invalid code!", 400)
    if len(code) > MAX_CODE_LENGTH:
        return None, None, ("Code is too long!", 400)
    return language, code, None


def execute_for_response(language, code, input_text=""):
    try:
        return run_code(language, code, input_text)
    except subprocess.TimeoutExpired:
        return "Code execution timed out!"
    except FileNotFoundError as error:
        return f"Could not run executable: {error.filename}\nCorrect compiler/interpreter not installed on the machine!"
    except Exception:
        current_app.logger.exception("Code execution failed")
        return "An internal execution error occurred!"


@pages.post("/run")
def run():
    language, code, error = validate_run_request(request.get_json(silent=True))
    if error:
        return jsonify({"output": error[0]}), error[1]
    return jsonify({"output": execute_for_response(language, code, request.json.get("input", ""))})


@pages.post("/assessment/<assessment_id>/run-tests")
def run_tests(assessment_id):
    item = find_assessment(assessment_id)
    data = request.get_json(silent=True) or {}
    if item is None:
        return jsonify({"error": "Assessment not found"}), 404
    question = next((q for q in item["questions"] if q["id"] == data.get("question_id")), None)
    if question is None or question["response_type"] != "code_editor":
        return jsonify({"error": "Question not found"}), 404
    language, code, error = validate_run_request(data)
    if error:
        return jsonify({"error": error[0]}), error[1]
    config = question["response_config"]
    if not config.get("runnable_tests"):
        return jsonify({"error": "Tests are disabled for this question."}), 400
    if language not in config["supported_languages"]:
        return jsonify({"error": "Language is not enabled for this question."}), 400
    results = []
    for test in config.get("tests", []):
        output = execute_for_response(language, code, test.get("input", ""))
        actual = output.split("\n\nProcess finished with exit code ")[0].rstrip()
        expected = str(test.get("expected_output", "")).rstrip()
        passed = actual == expected
        results.append({"name": test.get("name", "Test"), "passed": passed,
                        "hidden": bool(test.get("hidden", False)),
                        "output": "Passed" if passed else ("Hidden test failed" if test.get("hidden") else output),
                        "expected": None if test.get("hidden") else expected})
    return jsonify({"tests": results, "passed": sum(result["passed"] for result in results),
                    "total": len(results)})


@pages.get("/editor")
def editor():
    editor_config = {"languages": LANGUAGES, "initialLanguage": "python",
                     "monacoBase": MONACO_BASE, "runUrl": url_for("pages.run")}
    return render_template("editor.html", problem_html=load_problem(), languages=LANGUAGES,
                           monaco_base=MONACO_BASE, editor_config=editor_config)
