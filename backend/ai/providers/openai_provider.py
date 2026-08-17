import os
import json
import httpx

class OpenAIProvider:
    name = "openai"

    def __init__(self):
        self.key = os.getenv("AI_API_KEY", "")
        self.model = os.getenv("AI_MODEL", "gpt-4o-mini")

    async def analyze(self, task: str, context: dict):
        if not self.key:
            return {"provider": self.name, "status": "not_configured", "confidence": 0}
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "Return strict JSON only. Never guarantee profit. If data is insufficient, return NO_TRADE."},
                {"role": "user", "content": json.dumps({"task": task, "context": context})}
            ],
            "temperature": 0.1
        }
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {self.key}"},
                json=payload
            )
            r.raise_for_status()
            content = r.json()["choices"][0]["message"]["content"]
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                return {"provider": self.name, "status": "invalid_model_output", "confidence": 0}
