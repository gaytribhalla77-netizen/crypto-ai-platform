from datetime import datetime, timezone

class HealthRegistry:
    def __init__(self):
        self.components = {}

    def set(self, name, status, detail=""):
        self.components[name] = {"status":status,"detail":detail,"at":datetime.now(timezone.utc).isoformat()}

    def snapshot(self):
        return {"status":"ok" if self.components and all(x["status"]=="ok" for x in self.components.values()) else "degraded",
                "components":self.components}


# Process-wide singleton. Workers and API routes must share one registry —
# otherwise a worker's health checks are invisible to anyone calling
# GET /api/v09-15/health, which was silently the case before (each caller
# constructed its own empty HealthRegistry()).
health_registry = HealthRegistry()
