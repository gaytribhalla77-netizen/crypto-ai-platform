from __future__ import annotations
from dataclasses import dataclass,asdict
from time import time

@dataclass
class CertificationResult:
    name:str
    required:int
    executed:int
    passed:bool
    reason:str

def build_certification_plan():
    return [
        CertificationResult('sandbox_order_matrix',1000,0,False,'Requires authorized real broker sandbox credentials; no fake executions.'),
        CertificationResult('reconciliation_fault_matrix',100,0,False,'Requires broker sandbox responses to validate timeout/duplicate/partial-fill cases.'),
        CertificationResult('historical_walk_forward',10000,0,False,'Requires supplied historical dataset; no synthetic certification.'),
        CertificationResult('paper_trading',30,0,False,'Requires real market-data/paper account run over time.'),
    ]
