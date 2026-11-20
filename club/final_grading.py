"""Durable final grading queue; claim briefly, execute outside SQLite transactions."""
import hashlib
import json
import threading
import time
import uuid

from .store import database, expire, unpack


def grade_next(app):
    from .routes import find_assessment
    from .grading import grade_response
    with app.app_context():
        with database() as db:
            expire(db)
            # A lease recovers jobs interrupted by a server restart/worker failure.
            row = db.execute("SELECT * FROM attempts WHERE submitted IS NOT NULL AND "
                             "(grading_status='pending' OR (grading_status LIKE 'running:%' AND grading_started<?)) "
                             "ORDER BY submitted LIMIT 1", (time.time() - 3600,)).fetchone()
            if not row:
                return False
            attempt = unpack(row)
            claim = 'running:' + uuid.uuid4().hex
            db.execute('UPDATE attempts SET grading_status=?, grading_started=? WHERE id=?',
                       (claim, time.time(), attempt['id']))
        score = {}
        errors = []
        try:
            item = json.loads(attempt['definition']) if attempt.get('definition') else find_assessment(attempt['assessment'])
            if item is None:
                raise ValueError('Assessment definition is missing')
            for question in item['questions']:
                config = question['response_config']
                grader = config.get('grader', {})
                if not grader.get('code'):
                    continue
                language, code = None, ''
                if question['response_type'] == 'code_editor':
                    drafts = attempt['answers'].get(question['id'], {})
                    language = attempt['languages'].get(question['id'])
                    if language not in config['supported_languages']:
                        language = next((key for key in drafts if key in config['supported_languages']), config['supported_languages'][0])
                    code = drafts.get(language, config.get('default_code', {}).get(language, ''))
                try:
                    result = grade_response(language, code, grader, attempt['answers'])
                    score[question['id']] = {'earned': result['earned'], 'maximum': result['maximum']}
                    if language:
                        score[question['id']].update(language=language, code_sha256=hashlib.sha256(code.encode()).hexdigest())
                    if result['assessment_score'] is not None:
                        score['_assessment'] = result['assessment_score']
                except Exception as error:
                    # One broken grader must not prevent the other programs from running.
                    errors.append(f"{question['id']}: {type(error).__name__}: {error}")
                    app.logger.exception('Final grader failed for %s', question['id'])
        except Exception as error:
            errors.append(str(error))
        with database() as db:
            db.execute('UPDATE attempts SET score=?, grading_status=?, grading_error=? WHERE id=? AND grading_status=?',
                       (json.dumps(score), 'error' if errors else 'complete', '\n'.join(errors) or None, attempt['id'], claim))
        return True


def start_worker(app):
    def work():
        while True:
            try:
                if grade_next(app):
                    continue
            except Exception:
                app.logger.exception('Final grading queue failed')
            time.sleep(2)
    threading.Thread(target=work, name='final-grading', daemon=True).start()
