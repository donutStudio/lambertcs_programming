"""Load problem statements for server-side rendering."""
import markdown

from .config import PROBLEM_FILE


def load_problem():
    return markdown.markdown(
        PROBLEM_FILE.read_text(encoding="utf-8"),
        extensions=["fenced_code", "tables"],
    )
