from pathlib import Path
import importlib.util
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
TOOLS_PATH = ROOT / "src" / "analytics" / "product_tools.py"
WF_PATH = ROOT / "src" / "agents" / "workflow.py"

def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def test_product_tools_known_product():
    mod = load(TOOLS_PATH, "product_tools")
    risk = mod.get_product_risk("P1029")
    assert risk["product_id"] == "P1029"

def test_product_workflow():
    tools_mod = load(TOOLS_PATH, "product_tools")
    wf_mod = load(WF_PATH, "workflow")

    class DummyTools:
        get_product_risk = staticmethod(tools_mod.get_product_risk)
        get_product_trend = staticmethod(tools_mod.get_product_trend)
        get_ticket_summary = staticmethod(tools_mod.get_ticket_summary)
        search_product_knowledge = staticmethod(
            lambda question, product_id, top_k: {"sources": []}
        )

    result = wf_mod.ProductPulseWorkflow(DummyTools()).run(
        "P1029", "Why is this product high risk?"
    )
    assert result["product_id"] == "P1029"
    assert result["answer"]["summary"]
