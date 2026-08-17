from sqlalchemy import select, update
from database.models import SecuritySetting

async def ensure_setting(session, user_id: int) -> SecuritySetting:
    row = (await session.execute(select(SecuritySetting).where(SecuritySetting.user_id == user_id))).scalar_one_or_none()
    if row is None:
        row = SecuritySetting(user_id=user_id, kill_switch=False)
        session.add(row); await session.commit(); await session.refresh(row)
    return row

async def is_killed(session, user_id: int) -> bool:
    return bool((await ensure_setting(session, user_id)).kill_switch)

async def set_kill_switch(session, user_id: int, enabled: bool):
    await ensure_setting(session, user_id)
    await session.execute(update(SecuritySetting).where(SecuritySetting.user_id == user_id).values(kill_switch=enabled))
    await session.commit()
