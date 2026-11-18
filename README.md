# CS club programming

A small Flask website with server-rendered HTML/CSS and a Monaco code editor.

## Run locally

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000/ to choose an assessment. Each assessment presents its
questions in the existing editor interface.
Java needs `javac` and `java` on PATH; C++ needs `g++`. Monaco loads from its
existing CDN and requires internet access.

## Code layout

- `app.py`: server entry point.
- `club/__init__.py`: Flask application factory.
- `club/routes.py`: page rendering and submission validation.
- `club/execution.py`: compilation and execution.
- `club/problems.py`: Markdown problem loading.
- `club/languages.py`: language options, starter code, completion words.
- `club/config.py`: paths, execution limits, editor CDN location.
- `templates/`: assessments placeholder and editor pages.
- `static/`: styles and browser editor interactions.

Language data is rendered by Python into the editor page as JSON. JavaScript
handles Monaco, language switching, temporary per-language drafts, reset, and
sending code to the Python server. Drafts last until the page is refreshed.

## Checks

```powershell
python -m unittest discover -s tests -v
```

The current runner executes programs directly on the server machine; it is
intended for trusted local use. A temporary directory and timeout are not an
execution sandbox. Isolation is needed before accepting untrusted submissions.