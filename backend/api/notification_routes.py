from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from auth.dependencies import get_current_user, CurrentUser
from notifications import notifications

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


class NotificationRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4096)


@router.post("/test")
async def test_notification(body: NotificationRequest, user: CurrentUser = Depends(get_current_user)):
    results = await notifications.send(body.message, user_id=str(user.id))
    return {"results": [result.__dict__ for result in results]}
