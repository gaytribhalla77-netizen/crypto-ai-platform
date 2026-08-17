from __future__ import annotations
import asyncio
from collections import defaultdict

class EventBus:
    def __init__(self): self._subs=defaultdict(list)
    def subscribe(self,event_type,handler): self._subs[event_type].append(handler)
    async def publish(self,event_type,payload):
        for handler in list(self._subs.get(event_type,[])):
            result=handler(payload)
            if asyncio.iscoroutine(result): await result

event_bus=EventBus()
