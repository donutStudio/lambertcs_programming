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

Open http://127.0.0.1:5000/tryouts/. Monaco loads from its CDN. Java requires `javac`
and `java`; C++ requires `g++`. Use Python, Java, or C++ for either sample set.

The menu contains Lambert Competitive Programming Practice: student details,
instructions, then ten problems ordered from easier to harder. It is untimed,
requires no password, and allows unlimited attempts. The original tryout is
preserved outside the active assessments directory in `private_assessments/tryout_test/`. `/tryouts/editor` remains available by direct URL for
development, without a stimulus or menu link.

## Hosting path

`APP_URL_PREFIX` in `club/config.py` controls the public hosting path and defaults
to `/tryouts`. You can override it with the `APP_URL_PREFIX` environment variable
before starting Flask, or pass it to `create_app` in application configuration.
Use an empty string to serve at `/` instead. Restart the server after changing it.
Routes, static assets, frontend requests, navigation, and the session-cookie path
follow this setting. `/tryouts` redirects to `/tryouts/`.

When using a reverse proxy, forward `/tryouts/` and its subpaths to Flask with
the prefix intact. Flask handles the prefix itself; do not strip it or add it
again through `SCRIPT_NAME` or `X-Forwarded-Prefix`.

## Workspace

Drag the stimulus/response divider, explorer divider, or editor/output divider.
Dividers also accept arrow keys when focused. Files toggles the explorer. The
active source file follows the selected language, with a separate draft for each
language. Ctrl+Enter runs code. Alt+Left/Right changes questions.

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
[ASSESSMENT_FORMAT.md](ASSESSMENT_FORMAT.md#reference-sheets).

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

Accountless identification has limits. The device cookie is the primary identity.
The server records IP and browser user-agent and keeps a keyed hash of their
combination as a conservative quota signal. Deleting cookies cannot clear the
stored quota for that network/browser combination. A match never reveals saved
answers: without the original cookie, the student cannot resume the old attempt.
Different students using the same network and browser version can share this
quota; switching networks/browser or devices may evade it. No accountless IP or
device heuristic can guarantee one real person per attempt. Shared school networks
need an operator policy for resolving collisions. IPs are taken from the direct
connection, not client-supplied forwarding headers. Configure a trusted reverse
proxy deliberately before deploying; otherwise all proxied users may share its IP.

There is no public submissions export endpoint. Review/export on the server:

```powershell
.\.venv\Scripts\python.exe -m flask --app app list-submissions
.\.venv\Scripts\python.exe -m flask --app app show-submission ATTEMPT_ID
.\.venv\Scripts\python.exe -m flask --app app export-submissions --output submissions/export.csv
```

The CSV includes answers, server test results, timestamps, attempt/device IDs,
submission reason, IP, and browser details. Existing legacy JSON submissions are
left untouched; new attempts use SQLite. Test scores are calculated on the server,
and invalidated if tested code changes. Hidden test inputs/expected answers and
passcodes are not sent in the page configuration. Scores describe tests actually
run, not a separate final automatic grading pass.

## Assessment configuration

See [ASSESSMENT_FORMAT.md](ASSESSMENT_FORMAT.md) for JSON/folder/ZIP bundles,
text-file references, shared widget defaults, custom Python graders, score hooks,
and the practice bundle layout. The active menu follows assignments.json and contains only practice.

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
```

## Math in Markdown

Stimuli and short-answer prompts support KaTeX math: `$x_i^2$` or `\(x_i^2\)`
for inline expressions, and `$$\frac{a}{b}$$` or `\[\frac{a}{b}\]` for display
expressions. Display expressions can span lines. Code spans/blocks stay literal;
escape currency dollar signs as `\$`. In assessment JSON, double backslashes
(for example `"$\\frac{a}{b}$"`). KaTeX loads from a pinned CDN version; if it
cannot load, the original math source remains readable.
