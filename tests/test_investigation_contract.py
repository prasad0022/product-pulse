from pathlib import Path
import importlib.util

ROOT = Path(__file__).resolve().parents[1]

def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module

def test_investigation_contract():
    tools = load(ROOT / "src" / "analytics" / "product_tools.py", "product_tools")
    workflow = load(ROOT / "src" / "agents" / "workflow.py", "workflow")

    class DummyTools:
        get_product_risk = staticmethod(tools.get_product_risk)
        get_product_trend = staticmethod(tools.get_product_trend)
        get_ticket_summary = staticmethod(tools.get_ticket_summary)

    result = workflow.ProductPulseWorkflow(DummyTools()).run(
        "P1029", "Why is this product high risk?"
    )
    assert result["product_id"] == "P1029"
    assert "risk" in result["evidence"]
    assert "trend" in result["evidence"]
    assert "tickets" in result["evidence"]
