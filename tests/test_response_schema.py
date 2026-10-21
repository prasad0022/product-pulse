from pathlib import Path
import importlib.util

ROOT = Path(__file__).resolve().parents[1]

def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module

def test_investigation_response_schema():
    mod = load(ROOT / "src" / "rag" / "response_schema.py", "response_schema")
    payload = {
        "findings": ["Risk is elevated."],
        "evidence": ["Return rate increased."],
        "root_cause_candidates": ["Potential durability issue."],
        "recommended_actions": ["Inspect affected units."],
        "sources": [{"source_id": "D0001", "title": "Guide"}],
        "disclaimer": "Decision support only."
    }
    obj = mod.InvestigationResponse.model_validate(payload)
    assert obj.sources[0].source_id == "D0001"
