"""Read and normalize server-owned assessment definitions."""
import json
import copy
from pathlib import Path, PurePosixPath
from zipfile import ZipFile

from .config import BASE_DIR
from .references import normalize_references


class AssessmentParser:
    """Load and normalize the JSON files listed in assessments/assignments.json."""

    def __init__(self, directory=None):
        self.directory = Path(directory or BASE_DIR / "assessments")

    def load_all(self):
        index = json.loads((self.directory / "assignments.json").read_text(encoding="utf-8"))
        return [self.load(name) for name in index.get("assessments", [])]

    def load(self, name):
        path = (self.directory / name).resolve()
        if not path.is_relative_to(self.directory.resolve()):
            raise ValueError("Assessment paths must stay inside the assessments folder")
        if path.suffix.lower() == ".zip":
            with ZipFile(path) as archive:
                names = [entry.filename for entry in archive.infolist() if not entry.is_dir()]
                if len(names) != len(set(names)) or len(names) > 1000 or sum(e.file_size for e in archive.infolist()) > 64 * 1024 * 1024:
                    raise ValueError("Archive exceeds limits or contains duplicate paths")
                for entry in names:
                    if "\\" in entry or PurePosixPath(entry).is_absolute() or ".." in PurePosixPath(entry).parts or ":" in entry:
                        raise ValueError("Unsafe archive path")
                manifests = [n for n in names if PurePosixPath(n).name == "assessment.json"]
                if not manifests:
                    manifests = [n for n in names if n.endswith(".json")]
                if len(manifests) != 1:
                    raise ValueError("ZIP needs one assessment.json (or one unambiguous JSON manifest)")
                base = PurePosixPath(manifests[0]).parent
                def read_asset(name):
                    relative = PurePosixPath(name)
                    if relative.is_absolute() or ".." in relative.parts or "\\" in name or ":" in name:
                        raise ValueError("Asset paths must stay inside the assessment folder")
                    return archive.read(str(base / relative)).decode("utf-8-sig")
                data = self.resolve(json.loads(archive.read(manifests[0]).decode("utf-8-sig")), read_asset)
        else:
            if path.is_dir():
                candidates = [path / "assessment.json"] if (path / "assessment.json").exists() else list(path.glob("*.json"))
                if len(candidates) != 1:
                    raise ValueError("Folder needs assessment.json or one unambiguous JSON file")
                path = candidates[0]
            root = path.parent.resolve()
            def read_asset(name):
                asset = (root / name).resolve()
                if not asset.is_relative_to(root):
                    raise ValueError("Asset paths must stay inside the assessment folder")
                return asset.read_bytes().decode("utf-8-sig")
            data = self.resolve(json.loads(path.read_text(encoding="utf-8-sig")), read_asset)
        data.setdefault("time_limit_seconds", 0)
        data.setdefault("submittable_early", True)
        data.setdefault("auto_submit_on_leave", False)
        data.setdefault("passcode", "")
        data.setdefault("number_of_attempts", 1)
        data.setdefault("required_credentials", [])
        if (not isinstance(data['required_credentials'], list) or
                any(key not in ('full_name', 'email', 'student_id') for key in data['required_credentials'])):
            raise ValueError('required_credentials must contain full_name, email, or student_id')
        data.setdefault("score_visibility", {})
        data["score_visibility"].setdefault("while_taking", False)
        data["score_visibility"].setdefault("upon_completion", True)
        data["score_visibility"].setdefault("score_format", "fraction")
        data["stimuli"] = data.get("stimuli", {})
        normalize_references(data)
        for question in data.get("questions", []):
            config = copy.deepcopy(data.get("response_defaults", {}).get(question["response_type"], {}))
            supplied = question.get("response_config", {})
            for key, value in supplied.items():
                if isinstance(value, dict) and isinstance(config.get(key), dict): config[key].update(value)
                else: config[key] = value
            question["response_config"] = config
            config.setdefault("score_max", config.get("grader", {}).get("max_score", 0))
            response_type = question.get("response_type")
            if response_type == "code_editor":
                config = question["response_config"]
                if not config.get("supported_languages"):
                    raise ValueError("code_editor requires supported_languages")
                for setting, default in (("intellisense", True), ("runnable", True),
                                         ("runnable_tests", True), ("output", True),
                                         ("allow_input", True), ("file_browser", False),
                                         ("read_only", False)):
                    config.setdefault(setting, default)
                config.setdefault("default_code", {})
                config.setdefault("files", [])
                if "tests" in config:
                    raise ValueError("Legacy tests lists are unsupported; use grader.code and grader.assets")
                config.setdefault("grader", {})
                config.setdefault("score_max", config["grader"].get("max_score", 0))
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

    @classmethod
    def resolve(cls, value, read_asset):
        """A {$file: path} value is text, never another JSON parse or interpolation."""
        if isinstance(value, dict):
            if set(value) == {"$file"}:
                return read_asset(value["$file"])
            return {key: cls.resolve(item, read_asset) for key, item in value.items()}
        if isinstance(value, list):
            return [cls.resolve(item, read_asset) for item in value]
        return value
