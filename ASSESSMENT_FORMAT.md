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

The current tryout is:

```text
assessments/tryout_test/
  assessment.json
  instructions.md
  odd_ones_out.md
  swapped_spelling.md
  academic_comeback.md
  starter_code/          # three .py, three .java, three .cpp files
  tests/                # three Python graders and three case-data .txt files
```

The first question collects full name/email/student ID, then instructions, then
Odd Ones Out, Swapped Spelling, Academic Comeback. Question IDs stay stable when
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
