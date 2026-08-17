import asyncio
import json
import os
import time
from typing import Any

import httpx


class FallbackProviderChain:
    """Provider-independent AI gateway with fallback and optional consensus.

    Missing credentials and provider failures are skipped. If no provider can
    produce a valid decision, the result is always NO_TRADE.
    """

    def __init__(self) -> None:
        self.order = [
            p.strip().lower()
            for p in os.getenv(
                "AI_PROVIDER_FALLBACKS", "groq,gemini,openrouter,openai"