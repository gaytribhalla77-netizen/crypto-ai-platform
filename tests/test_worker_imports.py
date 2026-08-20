def test_background_worker_modules_import():
    from workers.health_monitor import HealthMonitorWorker
    from workers.market_scanner import market_scanner
    from workers.position_monitor import PositionMonitorWorker
    from workers.order_reconciliation import OrderReconciliationWorker

    assert HealthMonitorWorker is not None
    assert market_scanner is not None
    assert PositionMonitorWorker is not None
    assert OrderReconciliationWorker is not None
