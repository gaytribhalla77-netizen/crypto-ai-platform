from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends

from auth.dependencies import get_current_user
from monitoring.realtime import RealtimeIntelligence
from core.config import settings

router = APIRouter(prefix="/api/realtime", tags=["realtime"])
_monitor = RealtimeIntelligence(settings.watchlist_symbols)


@router.get("/status")
async def realtime_status(user=Depends(get_current_user)):
    return _monitor.snapshot()


@router.websocket("/stream")
async def realtime_stream(websocket: WebSocket):
    # Authenticate with the first WebSocket message instead of a query-string
    # token, so access tokens do not end up in browser/proxy URLs or logs.
    await websocket.accept()
    try:
        import asyncio
        from auth.security import decode_access_token
        message = await asyncio.wait_for(websocket.receive_json(), timeout=10)
        token = message.get("token")
        if not token:
            await websocket.close(code=4401)
            return
        decode_access_token(token)
    except Exception:
        await websocket.close(code=4401)
        return

    if not _monitor.running:
        await _monitor.start()
    q = _monitor.subscribe()
    try:
        await websocket.send_json({"type": "snapshot", "payload": _monitor.snapshot()})
        while True:
            event = await q.get()
            await websocket.send_json(event)
    except WebSocketDisconnect:
        pass
    finally:
        _monitor.unsubscribe(q)
