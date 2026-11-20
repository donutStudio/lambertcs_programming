"""Host-only administration. Run python admin_tools.py --help from the project root.

Review commands use only Python's standard library; no venv activation is needed.
"""
from __future__ import print_function

import os
import sys

# Keep this file parseable by Oracle Linux 7's Python 2.7. Re-exec before
# importing modern modules so `python admin_tools.py ...` works there too.
if sys.version_info < (3, 9):
    runtime = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.venv',
                           'Scripts' if os.name == 'nt' else 'bin',
                           'python.exe' if os.name == 'nt' else 'python')
    if os.path.isfile(runtime) and os.path.realpath(runtime) != os.path.realpath(sys.executable):
        os.execv(runtime, [runtime, os.path.abspath(__file__)] + sys.argv[1:])
    sys.exit('Use Python 3.9+ or create a project .venv with Python 3.9+ first.')

import argparse
import csv
from datetime import datetime
import json
from pathlib import Path
import shutil
import sqlite3
import subprocess
import time

ROOT = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database', type=Path, default=Path(os.environ.get('ATTEMPT_DATABASE', ROOT / 'submissions' / 'attempts.sqlite3')))
    sub = parser.add_subparsers(dest='command', required=True)
    for command in ('list', 'export'):
        cmd = sub.add_parser(command, help='Filter attempts by assessment, device, or student details')
        for key in ('assessment', 'device', 'name', 'email', 'student-id'):
            cmd.add_argument('--' + key)
        cmd.add_argument('--status', choices=['active', 'submitted', 'timeout', 'pending', 'complete', 'error'])
        cmd.add_argument('--since', help='Include attempts with activity since this ISO timestamp (timezone required)')
        if command == 'export':
            cmd.add_argument('--output', type=Path, default=ROOT / 'submissions' / 'export.csv')
            cmd.add_argument('--format', choices=['csv', 'json'], default='csv')
    sub.add_parser('show').add_argument('attempt_id')
    sub.add_parser('doctor', help='Show database and Python/runtime locations')
    sub.add_parser('backup', help='Make a consistent SQLite backup').add_argument('--output', type=Path, required=True)
    reset = sub.add_parser('reset-device', help="Delete only this device's attempts (optionally one assessment)")
    reset.add_argument('device_id'); reset.add_argument('--assessment'); reset.add_argument('--confirm', action='store_true')
    delete = sub.add_parser('delete-attempt', help='Delete one attempt, restoring one quota slot')
    delete.add_argument('attempt_id'); delete.add_argument('--confirm', action='store_true')
    regrade = sub.add_parser('regrade', help='Queue a submitted attempt for final grading')
    regrade.add_argument('attempt_id')
    sub.add_parser('grade-pending', help='Run queued graders locally using the project venv automatically')
    sub.add_parser('reload', help='Validate assessment files; new requests see updates without restarting the server')
    args = parser.parse_args()
    since = None
    if getattr(args, 'since', None):
        try:
            stamp = datetime.fromisoformat(args.since)
            if stamp.tzinfo is None: raise ValueError()
            since = stamp.timestamp()
        except ValueError:
            parser.error('--since requires an ISO timestamp with timezone, e.g. 2026-11-19T11:50:00-05:00')
    args.database = args.database.resolve()
    venv = ROOT / '.venv' / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
    if args.command == 'doctor':
        print('Python:', sys.executable, sys.version.split()[0])
        print('Project venv:', venv, '(found)' if venv.exists() else '(missing)')
        print('Database:', args.database, '(found)' if args.database.exists() else '(missing; start the app first)')
        for name in ('java', 'javac', 'g++'):
            print(name + ':', shutil.which(name) or 'not on PATH')
        return
    if args.command == 'reload':
        runtime = str(venv) if venv.exists() else sys.executable
        command = ('from club.assessments import AssessmentParser; '
                   'items=AssessmentParser().load_all(); '
                   'ids=[item["id"] for item in items]; '
                   'assert len(ids)==len(set(ids)), "Duplicate assessment IDs"; '
                   'print("Validated %d assessments. Updates are read automatically; no restart needed." % len(items))')
        raise SystemExit(subprocess.call([runtime, '-c', command], cwd=str(ROOT)))
    if args.command == 'grade-pending':
        runtime = str(venv) if venv.exists() else sys.executable
        command = ('from pathlib import Path; from club import create_app; '
                   'from club.final_grading import grade_next; '
                   'import sys; app=create_app({"TESTING":True,"ATTEMPT_DATABASE":Path(sys.argv[1])}); '
                   '\nwhile grade_next(app): pass\n')
        raise SystemExit(subprocess.call([runtime, '-c', command, str(args.database)], cwd=str(ROOT)))
    if not args.database.exists():
        parser.error('Database not found. Start the website first, or use --database PATH before the command.')
    with sqlite3.connect(str(args.database), timeout=30) as db:
        db.row_factory = sqlite3.Row
        if args.command == 'backup':
            args.output.parent.mkdir(parents=True, exist_ok=True)
            if args.output.resolve() == args.database:
                parser.error('Backup output must differ from the database.')
            if args.output.exists():
                parser.error('Backup output already exists; choose a new filename.')
            with sqlite3.connect(str(args.output)) as destination:
                db.backup(destination)
            print('Saved backup:', args.output)
            return
        if args.command in ('reset-device', 'delete-attempt'):
            if not args.confirm:
                parser.error('Deletion requires --confirm. Use backup first if records must be retained.')
            if args.command == 'reset-device':
                sql, values = 'DELETE FROM attempts WHERE owner=?', [args.device_id]
                if args.assessment:
                    sql += ' AND assessment=?'; values.append(args.assessment)
            else:
                sql, values = 'DELETE FROM attempts WHERE id=?', [args.attempt_id]
            count = db.execute(sql, values).rowcount
            print('Deleted', count, 'attempt(s). Device cookies remain usable.')
            return
        if args.command == 'regrade':
            columns = {row['name'] for row in db.execute('PRAGMA table_info(attempts)')}
            if 'grading_status' not in columns:
                parser.error('Start the updated website once to migrate the database.')
            count = db.execute("UPDATE attempts SET grading_status='pending', grading_error=NULL WHERE id=? AND submitted IS NOT NULL AND grading_status NOT LIKE 'running:%'", (args.attempt_id,)).rowcount
            if not count:
                parser.error('No submitted, idle attempt found. Wait for any running grader to finish.')
            print('Queued. The website worker or grade-pending will grade it.')
            return
        # Materialize deadlines even if the web process is stopped.
        db.execute("UPDATE attempts SET submitted=deadline, reason='timeout' WHERE submitted IS NULL AND deadline IS NOT NULL AND deadline<=?", (time.time(),))
        rows = [dict(row) for row in db.execute('SELECT a.*, d.ip, d.user_agent FROM attempts a LEFT JOIN devices d ON d.id=a.owner ORDER BY a.started DESC')]
        for row in rows:
            for key in ('answers', 'score', 'credentials', 'languages'):
                row[key] = json.loads(row.get(key) or '{}')
        if args.command == 'show':
            row = next((row for row in rows if row['id'] == args.attempt_id), None)
            if row is None: parser.error('Attempt not found')
            print(json.dumps(row, indent=2, ensure_ascii=False))
            return
        def matches(row):
            if since is not None and max(row['started'], row['updated'], row['submitted'] or 0) < since: return False
            if args.assessment and args.assessment != row['assessment']: return False
            if args.device and args.device != row['owner']: return False
            for option, key in [('name', 'full_name'), ('email', 'email'), ('student_id', 'student_id')]:
                value = getattr(args, option)
                # Old submissions kept identity in short-answer fields.
                actual = row['credentials'].get(key, row['answers'].get('student:' + key, ''))
                if value and value.casefold() not in str(actual).casefold(): return False
            status = args.status
            if status == 'active': return row['submitted'] is None
            if status == 'submitted': return row['submitted'] is not None
            if status == 'timeout': return row['reason'] == 'timeout'
            if status: return row.get('grading_status') == status
            return True
        rows = [row for row in rows if matches(row)]
        if args.command == 'list':
            for row in rows:
                identity = row['credentials'] or {k: row['answers'].get('student:' + k, '') for k in ('full_name', 'email', 'student_id')}
                print(row['id'], row['assessment'], row['reason'] or 'in progress', 'device=' + row['owner'], json.dumps(identity, ensure_ascii=False), 'grading=' + row.get('grading_status', 'legacy'), 'score=' + json.dumps(row['score']))
            print(str(len(rows)) + ' attempt(s)')
        else:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            for row in rows:
                score = row['score']
                earned = (score['_assessment']['earned'] if '_assessment' in score else
                          sum(result.get('earned', 0) for result in score.values()))
                # An unfinished final grading pass is not a verified zero.
                row['total_score'] = (int(earned) if row['submitted'] is not None and
                                      row.get('grading_status', 'complete') == 'complete' else None)
            if args.format == 'json':
                args.output.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding='utf-8')
                print('Exported', len(rows), 'attempt(s) to', args.output)
                return
            keys = ['id', 'owner', 'assessment', 'full_name', 'email', 'student_id', 'total_score', 'started', 'deadline', 'submitted', 'updated', 'reason', 'grading_status', 'grading_error', 'answers', 'score', 'languages', 'ip', 'user_agent']
            def safe(value):
                if isinstance(value, dict): value = json.dumps(value, ensure_ascii=False)
                if isinstance(value, str) and value.startswith(('=', '+', '-', '@', '\t', '\r', '\n')): value = "'" + value
                return value
            with args.output.open('w', newline='', encoding='utf-8') as handle:
                writer = csv.writer(handle); writer.writerow(keys)
                for row in rows:
                    for key in ('full_name', 'email', 'student_id'):
                        row[key] = row['credentials'].get(key, row['answers'].get('student:' + key, ''))
                    writer.writerow([safe(row.get(key, '')) for key in keys])
            print('Exported', len(rows), 'attempt(s) to', args.output)


if __name__ == '__main__':
    main()
