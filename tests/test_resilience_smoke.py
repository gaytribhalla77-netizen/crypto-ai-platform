from monitoring.health import HealthRegistry


def test_health_registry_degrades_when_dependency_fails():
    registry = HealthRegistry()
    registry.set("database", "ok")
    registry.set("exchange", "error", "simulated dependency outage")
    snapshot = registry.snapshot()
    assert snapshot["status"] == "degraded"
    assert snapshot["components"]["exchange"]["status"] == "error"
