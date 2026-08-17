from abc import ABC, abstractmethod
from typing import Any

class AIProvider(ABC):
    name = "base"

    @abstractmethod
    async def analyze(self, task: str, context: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError
