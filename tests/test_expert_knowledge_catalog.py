import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
from knowledge.catalog import load_expert_catalog

def test_expert_catalog_is_nontrivial_and_structured():
    c = load_expert_catalog()
    assert c["version"]
    assert len(c["rules"]) >= 30
    assert all(r["principle"] and r["conditions"] and r["failure_conditions"] for r in c["rules"])

def test_catalog_has_core_safety_topics():
    topics = {r["topic"] for r in load_expert_catalog()["rules"]}
    assert {"risk", "news", "historical", "backtesting", "execution", "learning", "safety"}.issubset(topics)

def test_no_catalog_rule_claims_profit_guarantee():
    bad = ("guaranteed profit", "guarantee profit", "always wins")
    for r in load_expert_catalog()["rules"]:
        text = r["principle"].lower()
        assert not any(x in text for x in bad)
