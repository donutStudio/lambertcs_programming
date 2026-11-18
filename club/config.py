"""Paths and execution limits."""
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
PROBLEM_FILE = BASE_DIR / "problems" / "example" / "next_squares.md"
TIMEOUT = 5
MAX_CODE_LENGTH = 20000
MAX_OUTPUT_LENGTH = 10000
MONACO_BASE = "https://cdn.jsdelivr.net/npm/monaco-editor@0.52.0/min/"
