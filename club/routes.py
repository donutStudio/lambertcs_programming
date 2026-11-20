"""Assessment pages and server-owned, accountless attempt API."""
import copy
import hashlib
import hmac
import json
import secrets
import subprocess
import time
from urllib.parse import urlsplit

from flask import Blueprint, current_app, jsonify, render_template, request, session, url_for

from .assessments import AssessmentParser
from .config import MAX_CODE_LENGTH, MONACO_BASE
from .execution import run_code
from .languages import LANGUAGES
from .markdown_math import render_markdown
from .references import reference_name, reference_source, search_sections, split_sections
from .store import count_attempts, database, latest, owned, start

pages = Blueprint("pages", __name__)
parser = AssessmentParser()


@pages.before_request
def identify_device():
    if request.endpoint == "static":
        return
    if request.method == "POST":
        origin = request.headers.get("Origin")

        allowed_origins = {
            f"{request.scheme}://{request.host}",
            "https://playful-trifle-80d61d.netlify.app",
            "https://tryouts.lambertcs.club",
            "https://lambertcs.netlify.app",
        }

        if origin and origin not in allowed_origins:
            return jsonify(
                error="Cross-origin requests are not allowed."
            ), 403
    ip = request.remote_addr or "unknown"
    agent = request.headers.get("User-Agent", "")[:512]
    fingerprint = hmac.new(current_app.secret_key.encode(), f"{ip}|{agent}".encode(), hashlib.sha256).hexdigest()
    with database() as db:
        device = db.execute("SELECT id FROM devices WHERE id=?", (session.get("device"),)).fetchone()
        # Fingerprints restrict new attempts; they never grant access to private answers.
        device_id = device["id"] if device else secrets.token_hex(24)
        now = time.time()
        db.execute("INSERT INTO devices VALUES (?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET last_seen=excluded.last_seen, ip=excluded.ip, user_agent=excluded.user_agent",
                   (device_id, fingerprint, now, now, ip, agent))
    session["device"] = device_id
    session.permanent = True


def find_assessment(assessment_id):
    return next((item for item in parser.load_all() if item["id"] == assessment_id), None)


def assessment_for_device(assessment_id):
    with database() as db:
        attempt = latest(db, session['device'], assessment_id)
        if attempt and attempt['submitted'] is None and attempt.get('definition'):
            return json.loads(attempt['definition'])
    return find_assessment(assessment_id)


def public_assessment(item):
    references = [{"id": key, "name": reference_name(item, key),
                   "url": url_for("pages.reference_sheet", assessment_id=item["id"], sheet_id=key)}
                  for key in item.get("allowed_reference_sheets", [])]
    item = copy.deepcopy(item)
    item.pop("reference_sheets", None)
    item["references"] = references
    item["requires_passcode"] = bool(item.pop("passcode", ""))
    item.pop("response_defaults", None)
    for question in item["questions"]:
        config = question.get("response_config", {})
        config.pop("grader", None)
    return item


@pages.get("/api/assessment/<assessment_id>/references/<sheet_id>")
def reference_sheet(assessment_id, sheet_id):
    item = assessment_for_device(assessment_id)
    if item is None or sheet_id not in item.get("allowed_reference_sheets", []):
        return jsonify(error="Reference sheet not found"), 404
    sections = split_sections(reference_source(item, sheet_id))
    query = request.args.get("q")
    if query is not None:
        query = query.strip()
        if len(query) > 200:
            return jsonify(error="Search is limited to 200 characters"), 400
        result = {"results": search_sections(sections, query) if query else []}
    elif "section" in request.args:
        try:
            index = int(request.args["section"])
            if index < 0:
                raise ValueError
            section = sections[index]
        except (ValueError, IndexError):
            return jsonify(error="Reference section not found"), 404
        result = {"html": render_markdown(section["source"])}
    else:
        result = {"sections": [{"id": index, "title": section["title"]}
                               for index, section in enumerate(sections)]}
    response = jsonify(result)
    response.headers["Cache-Control"] = "no-store"
    return response


def public_attempt(attempt):
    return {key: attempt[key] for key in ("id", "started", "deadline", "submitted", "answers", "score", "reason", "languages", "grading_status")}


@pages.after_request
def prevent_stale_attempts(response):
    if request.path.startswith(url_for('pages.index').rstrip('/') + '/api/'):
        response.headers['Cache-Control'] = 'no-store'
    return response


def clean_credentials(item, values):
    import re
    if not isinstance(values, dict):
        raise ValueError('Enter your student details on the assignments page.')
    result = {}
    for key in item.get('required_credentials', []):
        value = values.get(key, '')
        if not isinstance(value, str) or not value.strip() or len(value) > 200:
            raise ValueError(f'Enter {key.replace("_", " ")} on the assignments page.')
        value = value.strip()
        if key == 'email' and not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', value):
            raise ValueError('Enter a valid personal email.')
        if key == 'student_id' and not re.fullmatch(r'[0-9]+', value):
            raise ValueError('Student ID must contain digits only.')
        result[key] = value
    return result


@pages.get("/")
def index():
    return render_template("index.html", assessments=[public_assessment(item) for item in parser.load_all()])


@pages.get("/api/assignments")
def assignments():
    result = {}
    with database() as db:
        for item in parser.load_all():
            attempt = latest(db, session["device"], item["id"])
            count = count_attempts(db, session["device"], item["id"])
            score_item = json.loads(attempt['definition']) if attempt and attempt.get('definition') else item
            score_text = None
            if attempt and attempt['submitted'] and score_item['score_visibility']['upon_completion']:
                if attempt['grading_status'] == 'error':
                    score_text = 'unavailable — administrator review needed'
                elif attempt['grading_status'] != 'complete':
                    score_text = 'waiting'
                else:
                    scores = attempt['score']
                    earned = sum(scores.get(q['id'], {}).get('earned', 0) for q in score_item['questions'])
                    maximum = sum(scores.get(q['id'], {}).get('maximum', q['response_config'].get('score_max', 0)) for q in score_item['questions'])
                    total = scores.get('_assessment', {'earned': earned, 'maximum': maximum})
                    earned, maximum = total['earned'], total['maximum']
                    fmt = score_item['score_visibility']['score_format']
                    score_text = f'{round(earned / maximum * 100) if maximum else 0}%' if fmt == 'percent' else f'{earned:g}' if fmt == 'integer' else f'{earned:g}/{maximum:g}'
            result[item["id"]] = {"count": count, "active": bool(attempt and attempt["submitted"] is None),
                                  "available": not item["number_of_attempts"] or count < item["number_of_attempts"],
                                  "score": score_text,
                                  "grading_status": attempt['grading_status'] if attempt else None}
    return jsonify(result)


@pages.get("/assessment/<assessment_id>")
def assessment(assessment_id):
    item = assessment_for_device(assessment_id)
    if item is None:
        return "Assessment not found", 404
    item = public_assessment(item)
    for question in item["questions"]:
        for field in question.get("response_config", {}).get("fields", []):
            field["question_html"] = render_markdown(field.get("question_text", ""))
    config = {"assessment": item, "languages": LANGUAGES, "monacoBase": MONACO_BASE,
              "baseUrl": url_for("pages.index").rstrip("/"),
              "homeUrl": url_for("pages.index"),
              "runUrl": url_for("pages.run"), "testsUrl": url_for("pages.run_tests", assessment_id=assessment_id),
              "attemptUrl": url_for("pages.begin_attempt", assessment_id=assessment_id),
              "stimuliHtml": {key: render_markdown(value)
                              for key, value in item.get("stimuli", {}).items()}}
    with database() as db:
        previous = latest(db, session['device'], assessment_id)
        config['resumeActive'] = bool(previous and previous['submitted'] is None)
    return render_template("assessment.html", assessment=item, config=config, monaco_base=MONACO_BASE)


@pages.post("/api/assessment/<assessment_id>/attempt")
def begin_attempt(assessment_id):
    item = assessment_for_device(assessment_id)
    if item is None:
        return jsonify(error="Assessment not found"), 404
    data = request.get_json(silent=True) or {}
    if not isinstance(data, dict):
        return jsonify(error="Invalid request"), 400
    with database() as db:
        previous = latest(db, session["device"], assessment_id)
        if previous and previous['submitted'] is None and previous.get('definition'):
            item = json.loads(previous['definition'])
        try:
            credentials = clean_credentials(item, data.get('credentials', {})) if not (previous and previous['submitted'] is None) else previous['credentials']
        except ValueError as error:
            return jsonify(error=str(error)), 400
        if not (previous and previous["submitted"] is None) and item["passcode"] and data.get("passcode") != item["passcode"]:
            return jsonify(error="Incorrect passcode"), 403
        try:
            attempt = start(db, session["device"], item, credentials)
        except ValueError as error:
            return jsonify(error=str(error)), 403
    return jsonify(attempt=public_attempt(attempt), server_time=time.time())


def clean_answers(item, answers):
    if not isinstance(answers, dict):
        raise ValueError("Answers must be an object")
    cleaned = {}
    for question in item["questions"]:
        c = question["response_config"]
        if question["response_type"] == "code_editor":
            value = answers.get(question["id"], {})
            if not isinstance(value, dict):
                raise ValueError("Invalid code answer")
            cleaned[question["id"]] = {language: code for language, code in value.items()
                                      if language in c["supported_languages"] and isinstance(code, str) and len(code) <= MAX_CODE_LENGTH}
        elif question["response_type"] == "short_answer":
            for index, field in enumerate(c.get("fields", [])):
                key = f'{question["id"]}:{field.get("id", index)}'
                value = answers.get(key, "")
                if not isinstance(value, str) or len(value) > field["character_limit"]:
                    raise ValueError("Invalid short answer")
                cleaned[key] = value
    return cleaned


@pages.route("/api/attempt/<attempt_id>", methods=["GET", "POST"])
def attempt_state(attempt_id):
    with database() as db:
        attempt = owned(db, attempt_id, session["device"])
        if attempt is None:
            return jsonify(error="Attempt not found"), 404
        item = json.loads(attempt['definition']) if attempt.get('definition') else find_assessment(attempt["assessment"])
        if request.method == "POST":
            data = request.get_json(silent=True)
            if not isinstance(data, dict):
                return jsonify(error="Invalid request"), 400
            if attempt["submitted"] is not None:
                return jsonify(attempt=public_attempt(attempt), server_time=time.time())
            if data.get("submit") and item["time_limit_seconds"] and not item["submittable_early"] and not (item["auto_submit_on_leave"] and data.get("reason") == "leave"):
                return jsonify(error="Early submission is disabled"), 403
            try:
                answers = clean_answers(item, data.get("answers", attempt["answers"]))
            except ValueError as error:
                return jsonify(error=str(error)), 400
            if data.get("submit"):
                import re
                for question in item["questions"]:
                    for index, field in enumerate(question.get("response_config", {}).get("fields", [])):
                        value = answers.get(f'{question["id"]}:{field.get("id", index)}', '')
                        if field.get("required") and not value.strip():
                            return jsonify(error=f'Complete {field.get("question_text", "required field")} before submitting.'), 400
                        if value and ((field.get("email") and not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", value)) or (field.get("numeric_only") and not value.isdecimal())):
                            return jsonify(error=f'Invalid {field.get("question_text", "answer")}'), 400
            now = time.time()
            languages = data.get('languages', attempt['languages'])
            if not isinstance(languages, dict):
                return jsonify(error='Invalid languages'), 400
            languages = {q['id']: languages[q['id']] for q in item['questions']
                         if q['response_type'] == 'code_editor' and languages.get(q['id']) in q['response_config']['supported_languages']}
            score = attempt["score"]
            if answers != attempt["answers"]:
                score.pop("_assessment", None)
            for question_id, result in list(score.items()):
                if question_id == "_assessment":
                    continue
                if "language" not in result:
                    if answers != attempt["answers"]: del score[question_id]
                    continue
                code = answers.get(question_id, {}).get(result["language"], "")
                if hashlib.sha256(code.encode()).hexdigest() != result["code_sha256"]:
                    del score[question_id]
            db.execute("UPDATE attempts SET answers=?, updated=?, submitted=?, reason=?, score=?, languages=? WHERE id=?",
                       (json.dumps(answers), now, now if data.get("submit") else None,
                        "leave" if data.get("reason") == "leave" and data.get("submit") else "submitted" if data.get("submit") else None, json.dumps(score), json.dumps(languages), attempt_id))
            attempt = owned(db, attempt_id, session["device"])
    return jsonify(attempt=public_attempt(attempt), server_time=time.time())


def validate_run_request(data):
    if not isinstance(data, dict):
        return None, None, ("Invalid request!", 400)
    language, code = data.get("language"), data.get("code")
    if not isinstance(language, str) or language not in LANGUAGES:
        return None, None, ("Unsupported language.", 400)
    if not isinstance(code, str) or len(code) > MAX_CODE_LENGTH:
        return None, None, ("Invalid code or code is too long!", 400)
    return language, code, None


def execution_allowed():
    return request.remote_addr in ("127.0.0.1", "::1") or current_app.config["ALLOW_UNSAFE_REMOTE_EXECUTION"]


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
    if not execution_allowed():
        return jsonify(error="Remote execution requires an isolated runner."), 503
    data = request.get_json(silent=True)
    language, code, error = validate_run_request(data)
    if error:
        return jsonify(output=error[0]), error[1]
    input_text = data.get("input", "")
    if not isinstance(input_text, str) or len(input_text) > MAX_CODE_LENGTH:
        return jsonify(error="Invalid input"), 400
    return jsonify(output=execute_for_response(language, code, input_text))


@pages.post("/assessment/<assessment_id>/run-tests")
def run_tests(assessment_id):
    if not execution_allowed():
        return jsonify(error="Remote execution requires an isolated runner."), 503
    item = assessment_for_device(assessment_id)
    data = request.get_json(silent=True)
    language, code, error = validate_run_request(data)
    if error:
        return jsonify(error=error[0]), error[1]
    if item is None:
        return jsonify(error="Assessment not found"), 404
    question = next((q for q in item["questions"] if q["id"] == data.get("question_id")), None)
    if not question or question["response_type"] != "code_editor":
        return jsonify(error="Question not found"), 404
    c = question["response_config"]
    if not c["runnable_tests"] or language not in c["supported_languages"]:
        return jsonify(error="Tests or language disabled"), 403
    with database() as db:
        attempt = owned(db, data.get("attempt_id"), session["device"])
        if not attempt or attempt["assessment"] != assessment_id or attempt["submitted"] is not None:
            return jsonify(error="An active attempt is required"), 403
    original_code = attempt["answers"].get(question["id"], {}).get(language)
    if attempt.get('definition'):
        snapshot = json.loads(attempt['definition'])
        question = next(q for q in snapshot['questions'] if q['id'] == data.get('question_id'))
        c = question['response_config']
    from .grading import grade_response
    if not c.get("grader", {}).get("code"):
        return jsonify(error="No grader configured"), 400
    try:
        result = grade_response(language, code, c["grader"], attempt["answers"])
    except Exception:
        current_app.logger.exception("Assessment grader failed")
        return jsonify(error="The assessment grader failed; contact the administrator."), 500
    results = result["tests"]
    with database() as db:
        attempt = owned(db, attempt["id"], session["device"])
        if attempt["submitted"] is not None:
            return jsonify(error="Attempt has ended"), 409
        score = attempt["score"]
        current_code = attempt["answers"].get(question["id"], {}).get(language)
        if current_code != code and current_code != original_code:
            # A long-running grader must not overwrite a newer autosaved draft.
            return jsonify(tests=results, passed=sum(r["passed"] for r in results), total=len(results), score=score)
        score[question["id"]] = {"earned": result["earned"], "maximum": result["maximum"],
                                  "code_sha256": hashlib.sha256(code.encode()).hexdigest(), "language": language}
        if result["assessment_score"] is not None:
            score["_assessment"] = result["assessment_score"]
        answers = attempt["answers"]
        answers.setdefault(question["id"], {})[language] = code
        db.execute("UPDATE attempts SET score=?, answers=?, updated=? WHERE id=?",
                   (json.dumps(score), json.dumps(answers), time.time(), attempt["id"]))
    return jsonify(tests=results, passed=sum(r["passed"] for r in results), total=len(results), score=score)


@pages.get("/editor")
def editor():
    # Kept addressable for development; deliberately absent from the student menu.
    item = {"id": "standalone", "title": "Editor", "time_limit_seconds": 0,
            "score_visibility": {"while_taking": False, "upon_completion": False}, "questions": []}
    item["questions"] = [{"id": "editor", "response_type": "code_editor", "response_config": {
        "supported_languages": list(LANGUAGES), "default_code": {k: v["default_code"] for k, v in LANGUAGES.items()},
        "files": [], "runnable": True, "runnable_tests": False, "output": True, "allow_input": True,
        "file_browser": False, "read_only": False, "intellisense": True}}]
    config = {"assessment": item, "languages": LANGUAGES, "monacoBase": MONACO_BASE,
              "baseUrl": url_for("pages.index").rstrip("/"), "homeUrl": url_for("pages.index"),
              "runUrl": url_for("pages.run"), "stimuliHtml": {}, "standalone": True}
    return render_template("assessment.html", assessment=item, config=config, monaco_base=MONACO_BASE)


@pages.post("/api/diagnostics")
def check_code():
    if not execution_allowed():
        return jsonify(error="Remote diagnostics require an isolated runner."), 503
    language, code, error = validate_run_request(request.get_json(silent=True))
    if error:
        return jsonify(error=error[0]), error[1]
    from .interactive import diagnostics
    try:
        return jsonify(markers=diagnostics(language, code))
    except subprocess.TimeoutExpired:
        return jsonify(markers=[], message="Diagnostic check timed out")


@pages.post("/api/terminal")
def terminal_start():
    if not execution_allowed():
        return jsonify(error="Remote execution requires an isolated runner."), 503
    language, code, error = validate_run_request(request.get_json(silent=True))
    if error:
        return jsonify(error=error[0]), error[1]
    from .interactive import start_program
    try:
        return jsonify(id=start_program(session["device"], language, code))
    except ValueError as error:
        return jsonify(error=str(error)), 429


@pages.route("/api/terminal/<terminal_id>", methods=["GET", "POST"])
def terminal_io(terminal_id):
    from .interactive import SESSIONS
    program = SESSIONS.get(terminal_id)
    if not program or program.owner != session["device"]:
        return jsonify(error="Program not found"), 404
    if request.method == "POST":
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return jsonify(error="Invalid request"), 400
        if data.get("stop"):
            program.stop()
        elif data.get("eof"):
            if program.process and program.process.stdin and not program.process.stdin.closed:
                program.process.stdin.close()
        else:
            value = data.get("input")
            if not isinstance(value, str) or len(value) > 4096:
                return jsonify(error="Invalid input"), 400
            if not program.process or program.done or program.process.stdin.closed:
                return jsonify(error="Program is not accepting input"), 409
            try:
                program.append(value)
                program.process.stdin.write(value)
                program.process.stdin.flush()
            except (OSError, ValueError):
                return jsonify(error="Program has finished"), 409
    with program.lock:
        return jsonify(output=program.output, done=program.done,
                       ready=bool(program.process and program.process.stdin and not program.process.stdin.closed and not program.done))
