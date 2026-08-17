import asyncio

from monitoring.realtime import RealtimeIntelligence


def test_realtime_snapshot_is_read_only_and_empty_by_default():
    m = RealtimeIntelligence(("BTCUSDT",))
    snap = m.snapshot()
    assert snap["running"] is False
    assert snap["symbols"] == ["BTCUSDT"]
    assert snap["recent_events"] == []


def test_market_event_updates_latest_without_trading_side_effect():
    async def run():
        m = RealtimeIntelligence(("BTCUSDT",))
        await m._on_market_event({"data": {"s": "BTCUSDT", "b": "100", "a": "101"}})
        snap = m.snapshot()
        assert snap["latest"]["BTCUSDT"]["mid"] == 100.5
        assert snap["latest"]["BTCUSDT"]["spread"] == 1.0
        assert snap["recent_events"][-1]["type"] == "market_tick"
    asyncio.run(run())


def test_subscriber_queue_receives_events():
    async def run():
        m = RealtimeIntelligence(("BTCUSDT",))
        q = m.subscribe()
        await m._publish({"type": "market_alert", "symbol": "BTCUSDT"})
        event = await asyncio.wait_for(q.get(), 0.2)
        assert event["type"] == "market_alert"
        m.unsubscribe(q)
    asyncio.run(run())
