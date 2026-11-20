# Assessment bundles and custom grading

`assessments/assignments.json` lists paths relative to `assessments/`. Each entry
may be a JSON manifest, a folder, or a ZIP. Folders/ZIPs should contain one
`assessment.json`; otherwise one unambiguous JSON file is accepted. A ZIP may
wrap its bundle in a single parent folder. Nothing is extracted to disk.

Any JSON value can be replaced with `{"$file": "relative/path.any-extension"}`.
The file is read as UTF-8 text **after** JSON parsing, preserving its newlines,
quotes, backslashes, and LaTeX. References stay inside the manifest's folder.
There is no file-extension allowlist. References do not parse another JSON file:
a tester can explicitly parse referenced data with `json.loads(ctx.assets["cases"])`.
ZIPs reject traversal/absolute paths, duplicate names, over 1,000 entries, or
more than 64 MiB uncompressed content. These are server-admin artifacts, not
student uploads.

The active practice bundle is:

```text
assessments/practice_programming/
  assessment.json
  instructions.md
  candle_split.md        # plus nine more problem statements
  starter_code/          # ten .py, ten .java, ten .cpp files
  tests/                 # ten Python graders and ten case-data .txt files
```

The first question collects full name/email/student ID, then instructions, then
ten practice problems. Practice is untimed, has no passcode, and allows unlimited
attempts (`time_limit_seconds: 0`, `passcode: ""`, `number_of_attempts: 0`).
The original tryout is preserved in `private_assessments/tryout_test/`, outside
the loader's assessment directory, with its existing settings intact. To make it
available on tryout day, move that entire folder into `assessments/` and add
`"tryout_test"` to `assessments/assignments.json` after reviewing its settings.
The private folder is a local archive, not a student-facing assessment or static
asset; keep it out of any public source distribution.
Question IDs stay stable when
reordering. Common widget settings can live in `response_defaults`, keyed by
response type. Each question overrides those settings; nested configuration maps
merge one level (e.g. grader code/assets override its shared maximum).

```json
{
  "response_defaults": {
    "code_editor": {
      "supported_languages": ["python", "java", "cpp"],
      "grader": {"max_score": 100}
    }
  },
  "stimuli": {"example": {"$file": "example.md"}},
  "questions": [{
    "id": "example",
    "response_type": "code_editor",
    "stimulus": "example",
    "response_config": {
      "default_code": {"python": {"$file": "starter_code/example.py"}},
      "grader": {
        "code": {"$file": "tests/example.py"},
        "assets": {"cases": {"$file": "tests/example.txt"}}
      }
    }
  }]
}
```

## Reference sheets

Every assessment defaults to the three bundled Markdown references:
`py_reference` (Python), `java_reference` (Java), and `cpp_reference` (C++).
Set the top-level `allowed_reference_sheets` list to choose sheets and their menu
order. An explicit empty list `[]` disables references and hides the button.
Custom sheets are defined in the top-level `reference_sheets` object:

```json
{
  "allowed_reference_sheets": ["py_reference", "java_reference", "cpp_reference", "exam_notes"],
  "reference_sheets": {
    "exam_notes": {
      "name": "Exam notes",
      "content": {"$file": "references/exam_notes.md"}
    },
    "inline_example": {
      "name": "Units",
      "content": "# Units\n\n## Distance\n\nUse meters. $1\\text{ km}=1000\\text{ m}$."
    }
  }
}
```

`content` accepts an inline Markdown string or the same `{"$file": "..."}`
syntax as stimuli, including folder/ZIP bundles. Defining a sheet does not allow
it automatically: add its ID to `allowed_reference_sheets`. IDs must contain only
letters, digits, underscores, and hyphens; built-in IDs are reserved. Duplicate
or unknown allowed IDs and malformed custom sheets fail assessment loading.
The built-in source files live in `club/reference_sheets/`.

Reference opens a dropdown at the top left. Each chosen sheet opens in a separate
draggable, resizable window; choosing an open sheet brings it forward. Escape or
the close button closes it. Arrow keys on the title bar move it; arrow keys on
the resize handle resize it (Shift uses larger steps). Search is case-insensitive
literal text; selecting a result jumps to its section and highlights matches in
ordinary text/code. Mathematics renders with the same KaTeX support as stimuli.

The reader displays a continuous document, without collapsible sections. For lazy
delivery, use `##` headings between reasonably sized sections. The page contains
only allowed names/IDs/URLs; opening fetches section metadata, and scrolling loads
nearby sections. Offscreen sections release their DOM content while keeping their
measured heights. Search runs across the full sheet on the server and returns
section locations, counts, and excerpts, not the whole document. Closing aborts
requests and drops the window contents; responses are not cached by the browser.
A sheet without H2 headings works as one section and loads as a unit. Avoid
splitting a table, fenced code block, or shared Markdown link/footnote definition
across sections. References are trusted assessment-author content, like stimuli.

The old `tests: [{input, expected_output, ...}]` configuration is removed. Graders
are trusted Python code (inline strings or file references) defining `grade(ctx)`.
They run on the server and never come from a student's request. Their source,
assets, and private shared defaults are excluded from the public page config.
They have full host Python privileges: review bundles before installing them.

```python
def grade(ctx):
    # Optional convenience check: numbered automatically, points are configurable.
    ctx.check("13\n", "37", points=10, hidden=False, large=False,
              timeout=2, memory_mb=256, compile_timeout=30)

    # Or implement any comparison/partial credit rule yourself.
    result = ctx.run(ctx.assets["input"], timeout=0.5, memory_mb=128,
                     output_limit=50000, compile_timeout=30)
    if result.returncode == 0 and "desired" in result.output:
        ctx.award(5)
    # Alternative: ctx.set_score(earned, maximum=100)
    # Optional explicit total override: ctx.set_assessment_score(earned, maximum)
```

`ctx.run` returns `.output` (stdout), `.stderr`, `.returncode`, `.elapsed`,
`.timed_out`, `.memory_exceeded`, and `.output_exceeded`. The student source is
compiled once per grader invocation. Runtime excludes compilation. Limits apply
to each run; memory is sampled across the process tree with psutil. This local
monitor is not a hardened sandbox. Production still needs an isolated runner.
The output limit applies across stdout and stderr. `ctx.check` compares stdout
with trailing whitespace ignored, and adds `Test N` or `Test N (Large Input)`.
For wholly custom feedback, append `{name, passed, output, hidden}` dictionaries
to `ctx.tests`. Hidden checks do not expose actual output through the helper.

Starter prompts use **stderr** (`print(..., file=sys.stderr, flush=True)`,
`System.err.print`/`flush`, or `cerr << ... << flush`). The live terminal shows
stderr alongside stdout, while the grader compares stdout alone. Students should
keep prompts on stderr. C++ grade-list input ends with the terminal's EOF button.

`ctx.answers` holds the saved response values for custom scoring. Short-answer
widgets can also configure a `grader`; it runs on manual submission using these
answers, with no student program required. Required fields, email, and numeric
input are validated server-side on submission. Deadline expiry preserves the last
server-saved work; it does not run an additional grading pass.

The generic `Score:` display sums response scores, using each response's
`score_max` (defaults to `grader.max_score`) and the configured integer/fraction/
percent format. A grader may explicitly override the assessment total. Editing
code invalidates its score and any total override. Only the server awards points.

Host administration is documented in `admin_tools.py`. Examples:

```powershell
.\.venv\Scripts\python.exe admin_tools.py list
.\.venv\Scripts\python.exe admin_tools.py show ATTEMPT_ID
.\.venv\Scripts\python.exe admin_tools.py export --output submissions/export.csv
.\.venv\Scripts\python.exe admin_tools.py reset-device DEVICE_ID --confirm
```

`reset-device` intentionally resets the whole matching network/browser quota group;
it never silently deletes other device groups. Back up the database first.

Pane sizes are local UI preferences shared across questions and assessments,
with separate small-screen/desktop sizes. They do not affect attempts or scores.
File browser visibility defaults off and code defaults editable. `Files` toggles
visibility. Set `file_browser: true` to initially show it or `read_only: true` to
explicitly lock source editing.

Editor assistance provides standard-library auto-imports/includes, snippets,
member suggestions, hovers, and basic signatures. Java/C++ diagnostics use host
compilers; Python checks syntax, unused imports and likely undefined global names.
It is a practical completion layer, not Pylance or Java's full language server.

Checks:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
node tests/editor_behavior.cjs
```
## Student credentials and final grading

`required_credentials` defaults to `[]`. Set it to any subset of
`["full_name", "email", "student_id"]`. Required fields must be valid on the
assignments page before Start is enabled or a passcode is requested. The server
validates them again and stores a snapshot with each attempt. All bundled tryout
and practice sets require all three fields; the former student short-answer
question has been removed. These values are self-reported, without authentication.

All configured `grader.code` programs run after submission or timeout, regardless
of `runnable_tests` (which only controls the student's Run tests button). Final
grading uses each question's last saved selected language and source; an unopened
question uses its starter source. The dialog and assignment list show waiting
until grading completes, subject to score visibility. Python `input(prompt)`
prompts do not affect grading. Other stdout still counts as output; Java/C++
prompts should go to stderr. Final grading replaces provisional scores and runs
outside the database write transaction. Administrators can inspect grading errors
and request a regrade with `admin_tools.py`.
