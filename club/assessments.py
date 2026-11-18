"""Read and normalize server-owned assessment definitions."""
import json
from pathlib import Path

from .config import BASE_DIR


class AssessmentParser:
    """Load and normalize the JSON files listed in assessments/assignments.json."""

    def __init__(self, directory=None):
        self.directory = Path(directory or BASE_DIR / "assessments")

    def load_all(self):
        index = json.loads((self.directory / "assignments.json").read_text(encoding="utf-8"))
        return [self.load(name) for name in index.get("assessments", [])]

    def load(self, name):
        path = (self.directory / name).resolve()
        if path.parent != self.directory.resolve():
            raise ValueError("Assessment paths must stay inside the assessments folder")
        data = json.loads(path.read_text(encoding="utf-8"))
        data.setdefault("time_limit_seconds", 0)
        data.setdefault("submittable_early", True)
        data.setdefault("auto_submit_on_leave", False)
        data.setdefault("passcode", "")
        data.setdefault("number_of_attempts", 1)
        data.setdefault("score_visibility", {})
        data["score_visibility"].setdefault("while_taking", False)
        data["score_visibility"].setdefault("upon_completion", True)
        data["score_visibility"].setdefault("score_format", "fraction")
        data["stimuli"] = data.get("stimuli", {})
        for question in data.get("questions", []):
            question.setdefault("response_config", {})
            response_type = question.get("response_type")
            if response_type == "code_editor":
                config = question["response_config"]
                if not config.get("supported_languages"):
                    raise ValueError("code_editor requires supported_languages")
                for setting, default in (("intellisense", True), ("runnable", True),
                                         ("runnable_tests", True), ("output", True),
                                         ("allow_input", True), ("file_browser", True),
                                         ("read_only", False)):
                    config.setdefault(setting, default)
                config.setdefault("default_code", {})
                config.setdefault("files", [])
                config.setdefault("tests", [])
            elif response_type == "short_answer":
                for field in question["response_config"].get("fields", []):
                    field.setdefault("character_limit", 100)
                    field.setdefault("numeric_only", False)
                    field.setdefault("email", False)
            elif response_type == "stimulus_only":
                if question.get("stimulus") not in data["stimuli"]:
                    raise ValueError("stimulus_only requires a valid stimulus key")
            else:
                raise ValueError(f"Unsupported response_type: {response_type}")
        return data
