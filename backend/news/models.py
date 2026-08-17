from dataclasses import dataclass
from datetime import datetime

@dataclass
class NewsItem:
    source: str
    title: str
    url: str
    published_at: datetime
    asset: str | None
    impact: str = "UNKNOWN"
    confidence: float = 0.0
