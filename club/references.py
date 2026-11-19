"""Reference catalog and section-level delivery; document bodies stay server-side."""
import re
from html.parser import HTMLParser
from pathlib import Path

from .markdown_math import render_markdown

BUILTIN_REFERENCES = {
    "py_reference": "Python",
    "java_reference": "Java",
    "cpp_reference": "C++",
}
REFERENCE_DIRECTORY = Path(__file__).resolve().parent / "reference_sheets"


def normalize_references(assessment):
    custom = assessment.setdefault("reference_sheets", {})
    if not isinstance(custom, dict):
        raise ValueError("reference_sheets must be an object keyed by sheet ID")
    for sheet_id, sheet in custom.items():
        if not re.fullmatch(r"[A-Za-z0-9_-]+", sheet_id) or sheet_id in BUILTIN_REFERENCES:
            raise ValueError("Custom reference IDs must be URL-safe and cannot replace built-ins")
        if not isinstance(sheet, dict) or not isinstance(sheet.get("name"), str) or not sheet["name"].strip():
            raise ValueError("Each reference sheet requires a nonempty name")
        if not isinstance(sheet.get("content"), str):
            raise ValueError("Each reference sheet requires Markdown content (inline or $file)")
    allowed = assessment.setdefault("allowed_reference_sheets", list(BUILTIN_REFERENCES))
    if not isinstance(allowed, list) or any(not isinstance(key, str) for key in allowed):
        raise ValueError("allowed_reference_sheets must be a list of sheet IDs")
    if len(allowed) != len(set(allowed)) or any(key not in BUILTIN_REFERENCES and key not in custom for key in allowed):
        raise ValueError("Allowed reference IDs must exist and cannot be repeated")


def reference_name(assessment, sheet_id):
    return BUILTIN_REFERENCES.get(sheet_id) or assessment["reference_sheets"][sheet_id]["name"]


def reference_source(assessment, sheet_id):
    if sheet_id in BUILTIN_REFERENCES:
        return (REFERENCE_DIRECTORY / f"{sheet_id}.md").read_text(encoding="utf-8")
    return assessment["reference_sheets"][sheet_id]["content"]


def split_sections(source):
    """Split on H2 headings outside fenced code, keeping each section valid Markdown."""
    sections, lines, title, fence = [], [], "Overview", None
    for line in source.splitlines(keepends=True):
        marker = re.match(r"^ {0,3}(`{3,}|~{3,})(.*)$", line)
        if marker:
            run, tail = marker.groups()
            if fence is None:
                fence = run
            elif run[0] == fence[0] and len(run) >= len(fence) and not tail.strip():
                fence = None
        heading = re.match(r"^##\s+(.+?)\s*#*\s*$", line) if fence is None else None
        if heading:
            if "".join(lines).strip():
                sections.append({"title": title, "source": "".join(lines)})
            title, lines = heading[1], []
        lines.append(line)
    if "".join(lines).strip():
        sections.append({"title": title, "source": "".join(lines)})
    return sections


class TextReader(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, data):
        self.parts.append(data)


def search_sections(sections, query):
    results = []
    for index, section in enumerate(sections):
        # Search visible text, not Markdown fences or link destinations.
        reader = TextReader()
        reader.feed(render_markdown(section["source"]))
        text = " ".join(" ".join(reader.parts).split())
        matches = list(re.finditer(re.escape(query), text, re.IGNORECASE))
        if matches:
            position = matches[0].start()
            results.append({"section": index, "title": section["title"], "count": len(matches),
                            "excerpt": text[max(0, position - 45):position + len(query) + 90]})
    return results
