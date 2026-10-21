from pathlib import Path
import importlib.util

ROOT = Path(__file__).resolve().parents[1]

def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module

def test_api_health_contract():
    mod = load(ROOT / "api" / "main.py", "api_main")
    result = mod.health()
    assert result["status"] == "ok"
    assert "llm_provider" in result

def test_risk_contract():
    mod = load(ROOT / "api" / "main.py", "api_main")
    result = mod.product_risk("P1029")
    assert result["product_id"] == "P1029"
    assert result["risk_level"] in {"Low", "Medium", "High"}
