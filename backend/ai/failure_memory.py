from __future__ import annotations
from collections import Counter
from sqlalchemy import select
from database.models import AuditEvent
import json

class FailureMemory:
    """Persistent decision-outcome memory. It records patterns but cannot
    directly override the canonical risk firewall."""
    def __init__(self): self._events=[]
    def record(self, decision: str, correct: bool, regime: str, confidence: float, reason: str=''):
        self._events.append({'decision':decision,'correct':bool(correct),'regime':regime,'confidence':float(confidence),'reason':reason})
    def summary(self):
        if not self._events:return {'samples':0,'accuracy':None,'failure_patterns':[]}
        failures=[e for e in self._events if not e['correct']]; patterns=Counter((e['regime'],e['decision']) for e in failures)
        return {'samples':len(self._events),'accuracy':round(sum(e['correct'] for e in self._events)/len(self._events),4),'failure_patterns':[{'regime':k[0],'decision':k[1],'failures':v} for k,v in patterns.most_common()]}
    async def persist(self, session, user_id:int, decision:str, correct:bool, regime:str, confidence:float, reason:str=''):
        session.add(AuditEvent(user_id=user_id,event_type='ai_failure_memory',payload=json.dumps({'decision':decision,'correct':correct,'regime':regime,'confidence':confidence,'reason':reason})))
        await session.commit()
