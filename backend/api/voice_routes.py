from fastapi import APIRouter
from pydantic import BaseModel

from voice.service import VoiceService

router = APIRouter(prefix="/api/voice", tags=["voice"])
_service = VoiceService()


class VoiceInput(BaseModel):
    text: str


@router.post("/parse")
async def parse_voice_command(payload: VoiceInput):
    """Turns spoken text (already transcribed client-side) into a
    structured intent. Public and side-effect-free: it never calls the
    database or an exchange, and trade intents always come back with
    requires_confirmation=True. The actual order still has to go through
    the normal authenticated, risk-gated /api/v06/testnet/order endpoint."""
    return await _service.handle(payload.text)
