"""Server-owned attempts. Browser cookies identify guests, never hold attempt state."""
import json
import sqlite3
import time
import uuid
from contextlib import contextmanager

from flask import current_app


@contextmanager
def database():
    path = current_app.config["ATTEMPT_DATABASE"]
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, timeout=15)
    connection.row_factory = sqlite3.Row
    connection.execute("""CREATE TABLE IF NOT EXISTS attempts (
        id TEXT PRIMARY KEY, owner TEXT NOT NULL, assessment TEXT NOT NULL,
        started REAL NOT NULL, deadline REAL, submitted REAL,
        answers TEXT NOT NULL DEFAULT '{}', score TEXT NOT NULL DEFAULT '{}',
        updated REAL NOT NULL, reason TEXT)""")
    connection.execute("""CREATE TABLE IF NOT EXISTS devices (
        id TEXT PRIMARY KEY, fingerprint TEXT NOT NULL, first_seen REAL NOT NULL,
        last_seen REAL NOT NULL, ip TEXT, user_agent TEXT)""")
    try:
        connection.execute("BEGIN IMMEDIATE")
        columns = {row['name'] for row in connection.execute('PRAGMA table_info(attempts)')}
        for name, definition in [('credentials', "TEXT NOT NULL DEFAULT '{}'"),
                                 ('languages', "TEXT NOT NULL DEFAULT '{}'"),
                                 ('grading_status', "TEXT NOT NULL DEFAULT 'pending'"),
                                 ('grading_started', 'REAL'), ('grading_error', 'TEXT')]:
            if name not in columns:
                connection.execute(f'ALTER TABLE attempts ADD COLUMN {name} {definition}')
        if 'definition' not in columns:
            connection.execute('ALTER TABLE attempts ADD COLUMN definition TEXT')
        connection.execute('CREATE INDEX IF NOT EXISTS attempt_owner ON attempts(owner, assessment, started)')
        connection.execute('CREATE INDEX IF NOT EXISTS grading_queue ON attempts(grading_status, submitted)')
        yield connection
        connection.commit()
    finally:
        connection.close()


def expire(db):
    now = time.time()
    db.execute("UPDATE attempts SET submitted=deadline, reason='timeout' "
               "WHERE submitted IS NULL AND deadline IS NOT NULL AND deadline <= ?", (now,))


def unpack(row):
    if row is None:
        return None
    item = dict(row)
    for key in ("answers", "score", "credentials", "languages"):
        item[key] = json.loads(item[key])
    return item


def latest(db, owner, assessment):
    expire(db)
    return unpack(db.execute("SELECT * FROM attempts WHERE owner=? AND assessment=? "
                             "ORDER BY started DESC LIMIT 1", (owner, assessment)).fetchone())


def start(db, owner, item, credentials=None):
    previous = latest(db, owner, item["id"])
    if previous and previous["submitted"] is None:
        return previous
    count = count_attempts(db, owner, item["id"])
    if item["number_of_attempts"] and count >= item["number_of_attempts"]:
        raise ValueError("No attempts remaining.")
    now = time.time()
    attempt_id = uuid.uuid4().hex
    deadline = now + item["time_limit_seconds"] if item["time_limit_seconds"] else None
    db.execute("INSERT INTO attempts (id,owner,assessment,started,deadline,updated,credentials,definition) VALUES (?,?,?,?,?,?,?,?)",
               (attempt_id, owner, item["id"], now, deadline, now, json.dumps(credentials or {}), json.dumps(item)))
    return latest(db, owner, item["id"])


def count_attempts(db, owner, assessment):
    # Shared IPs and browser versions are not identities (especially behind a proxy).
    return db.execute('SELECT count(*) FROM attempts WHERE assessment=? AND owner=?',
                      (assessment, owner)).fetchone()[0]


def owned(db, attempt_id, owner):
    expire(db)
    return unpack(db.execute("SELECT * FROM attempts WHERE id=? AND owner=?", (attempt_id, owner)).fetchone())
