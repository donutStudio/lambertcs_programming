# CS club programming assessments

A Flask app with a compact dark assessment workspace, Monaco Editor, short
answers, standalone instructions, and server-owned accountless attempts.

## Run locally

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000/ (or your configured prefix). Monaco loads from its CDN. Java requires `javac`
and `java`; C++ requires `g++`. Use Python, Java, or C++ for either sample set.

The menu follows `assessments/assignments.json` and currently includes practice
and tryout sets A and B. Student details are entered on the assignments page;
all three bundled sets require name, personal email, and student ID. Each code
question has separate drafts for Python, Java, and C++. `/editor` is also available.

## Hosting path

`APP_URL_PREFIX` in `club/config.py` controls the public hosting path and defaults
to the domain root (`""`). You can override it with the `APP_URL_PREFIX` environment variable
before starting Flask, or pass it to `create_app` in application configuration.
Use an empty string to serve at `/` instead. Restart the server after changing it.
Routes, static assets, frontend requests, navigation, and the session-cookie path
follow this setting. When configured as `/tryouts`, `/tryouts` redirects to `/tryouts/`.

When using a reverse proxy, forward `/tryouts/` and its subpaths to Flask with
the prefix intact. Flask handles the prefix itself; do not strip it or add it
again through `SCRIPT_NAME` or `X-Forwarded-Prefix`.

## Workspace

Drag the stimulus/response divider, explorer divider, or editor/output divider.
Dividers also accept arrow keys when focused. Files toggles the explorer. The
active source file follows the selected language, with a separate draft for each
language. Reset asks for confirmation and can be undone with Ctrl+Z (Cmd+Z on Mac).
Exit is first in the top menu, followed by Reference. Submit appears only at the
end of the last question when early submission is allowed. Ctrl+Enter runs code. Alt+Left/Right changes questions.

Run starts a live process. Enter sends a line from inside Terminal, EOF (or
Ctrl+D) closes stdin, and Stop (or Ctrl+C) stops execution. Processes stop after
120 seconds or at the output limit. Changing questions stops the active program.
Check **Pretyped input** for the old batch-stdin behavior; it starts off unchecked.
Batch runs and tests retain the five-second execution timeout.

IntelliSense includes language suggestions and names from the current source.
Debounced diagnostics underline Python syntax errors and unused imports; Java
and C++ use installed compilers for errors/warnings without running the program.
These checks are best effort, not full language servers or a proof of correctness.

The top-left **Reference** menu opens Python, Java, and C++ quick references in
draggable, resizable windows with search and KaTeX. Documents load as you scroll.
Assessments can choose built-ins, add custom Markdown sheets (inline or `$file`),
or disable references with `allowed_reference_sheets: []`; see
[ASSESSMENT_FORMAT.MD](ASSESSMENT_FORMAT.MD#reference-sheets).

## Attempts and submissions

`submissions/attempts.sqlite3` stores device records, attempt counts, start times,
deadlines, drafts, submission status/reason, and verified test results. The browser
receives a signed HttpOnly, SameSite cookie containing only a random device ID.
The signing key persists in `submissions/.session-key`, or set `SECRET_KEY` in the
server environment. Back up the database and key together. Neither is committed.
Browser storage does not control attempts, deadlines, or scores. Drafts save
automatically; the toolbar reports failures and retries. A submission succeeds
only after the server acknowledges it. Late edits are rejected and attempts close
at their server deadline, even if the browser clock is changed or the page closes.
Expiry is materialized on the next server read/export; the deadline is authoritative.

Attempt quotas belong to the signed device cookie. IP addresses and browser
versions are retained for administration but never merge students' quotas.
Students on the same school network or reverse proxy therefore have separate
attempts. Keep the signing key stable across restarts and use the same hostname,
HTTPS, and URL prefix. Clearing cookies or using another browser creates a new
device; entered credentials are self-reported, not a login or proof of identity.

Final submission and deadline expiry queue every configured grader, including
questions where Run tests was never clicked. The completion dialog and assignment
list display **Score: waiting** until the server finishes. The selected language
is saved with the draft and used for final grading. The server checks deadlines
in the background even if the student closes the browser. Jobs survive restarts;
interrupted jobs are recovered after their one-hour lease. A grader error is shown
as unavailable and can be reviewed/requeued by an administrator. Scores respect
`score_visibility.upon_completion` on the assignment list and completion dialog.

Python `input("any prompt")` prompts are suppressed only during grading; the
interactive terminal still shows them. Actual stdout is compared exactly (apart
from trailing whitespace); arbitrary extra stdout is still incorrect output.
Java/C++ prompts should use stderr (`System.err` / `cerr`) as in the starters.

## Host administration (no venv activation)

From the project root, use `python admin_tools.py ...`. List, show, export,
backup, reset, and regrade use only the Python standard library. `grade-pending`
automatically uses `.venv/Scripts/python.exe` on Windows or `.venv/bin/python` on
Linux to load the grading dependencies. The website also processes this queue.
Use an installed Python 3.9 or newer for administration and the app.

On Windows PowerShell:

```powershell
cd C:\Users\thegy\Downloads\cs_club_programming
python admin_tools.py doctor
python admin_tools.py list --assessment tryout_test
python admin_tools.py list --email student@example.com
python admin_tools.py list --student-id 123456
python admin_tools.py list --name "Jane Doe"
python admin_tools.py show ATTEMPT_ID
python admin_tools.py export --since "2026-11-19T11:50:00-05:00" --output submissions/tryouts-nov19.csv
python admin_tools.py backup --output submissions/backup-nov19.sqlite3
python admin_tools.py reset-device DEVICE_ID --assessment tryout_test --confirm
python admin_tools.py delete-attempt ATTEMPT_ID --confirm
python admin_tools.py regrade ATTEMPT_ID
python admin_tools.py grade-pending
```

On this Oracle Linux 7.9 VM, `/usr/bin/python` is Python 2.7; use the existing
project Python 3.11 without activating its venv. A Bash function makes the same
`python admin_tools.py ...` commands work while leaving the OS Python alone:

```bash
ssh MonkeMatrix
cd /home/opc/lambertcs_programming
python() { /home/opc/lambertcs_programming/.venv/bin/python "$@"; }
python admin_tools.py doctor
python admin_tools.py list --email student@example.com
python admin_tools.py export --since '2026-11-19T11:50:00-05:00' --output submissions/tryouts-nov19.csv
python admin_tools.py backup --output submissions/backup-nov19.sqlite3
```

Put that function in `~/.bashrc` if you want it in later interactive SSH sessions,
then run `source ~/.bashrc`. It selects an interpreter; it does not activate the
venv. Alternatively run `.venv/bin/python admin_tools.py ...` directly. On another
Linux host with a modern system Python, use `python3 admin_tools.py ...` or point
the function at that interpreter. Do not replace Oracle Linux's `/usr/bin/python`.

`list` and `export` accept `--assessment`, `--device`, `--name`, `--email`,
`--student-id`, `--status`, and `--since`. Credential matching is case-insensitive
substring matching, including old `student:*` short answers. `--since` requires an
ISO timestamp with an explicit timezone and includes attempts started, saved, or
submitted at/after that instant (including attempts started earlier). CSV exports
include drafts and completed attempts, credentials, answers, scores, grading state,
IP/browser, and timestamps. Add `--format json` for a complete structured JSON export.
Timestamps in exported records are Unix seconds.
`show` displays the complete attempt as JSON. `backup` uses SQLite's consistent
backup API; choose a new filename. Keep backups and exports private.

The default database path is relative to this script's root, independent of your
current directory. Override it using `python admin_tools.py --database /path/to/attempts.sqlite3 list`,
or set `ATTEMPT_DATABASE` for both the app and tools. There is no public admin
endpoint. `reset-device` only deletes that device's attempts, optionally for one
assessment; it does not affect classmates sharing the network. Deletion requires
`--confirm`. Start the updated website once to migrate an older database before
using `regrade`. Final grading errors are recorded in `grading_error`.

To enter the existing server screen and run the app:

```bash
screen -r lambertcs_flask
cd /home/opc/lambertcs_programming
./app.sh
```

If the screen is already attached, use `screen -x lambertcs_flask` to share it.
`app.sh` exports `COOKIE_SECURE=1` and uses `exec` to start the requested Gunicorn
command in the foreground. Ctrl+C stops Gunicorn and returns to the screen shell;
Ctrl+A, then D detaches without stopping it. No venv activation is needed. Secure
cookies require HTTPS when accessing the site through its proxy.

## Assessment configuration

See [ASSESSMENT_FORMAT.MD](ASSESSMENT_FORMAT.MD) for JSON/folder/ZIP bundles,
text-file references, shared widget defaults, custom Python graders, score hooks,
and the bundle layout. The active menu follows assignments.json.

The old fixed test-case configuration has been replaced by trusted server-authored
graders. Their source and assets never go into the public page configuration.
Use `admin_tools.py --help` for dedicated host administration examples.

## Deployment boundary

The supplied subprocess runner executes code on its host. It is for trusted local
development, not untrusted student code. Remote execution/compilation is refused
by default. Before hosting on the club website, integrate an isolated execution
service for batch runs, live stdin, test runs, and compiler diagnostics. Do not
expose this local runner through a loopback reverse proxy: loopback checks do not
provide isolation. `ALLOW_UNSAFE_REMOTE_EXECUTION` exists only for explicitly
trusted testing environments, never as a production solution.

Run the web app behind a production WSGI server with HTTPS, set `COOKIE_SECURE=1`,
protect/back up the submissions directory, and configure trusted proxy headers.
Interactive process handles currently live in one server process, so use one
threaded worker for local testing; an external runner must own handles across
workers in production. Do not enable Flask debug mode on the public site.

## Checks

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
node --check static/assessment.js
node --check static/home.js
node tests/url_prefix.cjs
node tests/references_browser.cjs  # Requires Playwright and installed Chromium
node tests/assessment_browser.cjs  # Credentials, reset undo, submission and final scores
```

## Math in Markdown

Stimuli and short-answer prompts support KaTeX math: `$x_i^2$` or `\(x_i^2\)`
for inline expressions, and `$$\frac{a}{b}$$` or `\[\frac{a}{b}\]` for display
expressions. Display expressions can span lines. Code spans/blocks stay literal;
escape currency dollar signs as `\$`. In assessment JSON, double backslashes
(for example `"$\\frac{a}{b}$"`). KaTeX loads from a pinned CDN version; if it
cannot load, the original math source remains readable.