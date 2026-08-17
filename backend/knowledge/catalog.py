from __future__ import annotations
import json
from pathlib import Path

CATALOG_PATH = Path(__file__).parent / "data" / "expert_knowledge_pack.json"

def load_expert_catalog() -> dict:
    return json.loads(CATALOG_PATH.read_text(encoding="utf-8"))

def catalog_rules() -> list[dict]:
    return load_expert_catalog()["rules"]
