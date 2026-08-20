from fastapi import APIRouter
from pydantic import BaseModel, Field
from strategies.profit_rotation import RotationConfig, build_plan, manage_position

router = APIRouter(prefix='/api/strategy', tags=['strategy'])

class PlanInput(BaseModel):
    closes: list[float] = Field(min_length=30, max_length=5000)
    target_net_pct: float = Field(default=1.75, gt=0, le=10)
    max_loss_pct: float = Field(default=0.90, gt=0, le=5)
    fee_rate: float = Field(default=0.001, ge=0, le=0.02)
    slippage_rate: float = Field(default=0.0005, ge=0, le=0.02)

class PositionInput(BaseModel):
    entry: float = Field(gt=0)
    current: float = Field(gt=0)
    target_net_pct: float = Field(default=1.75, gt=0, le=10)
    max_loss_pct: float = Field(default=0.90, gt=0, le=5)
    fee_rate: float = Field(default=0.001, ge=0, le=0.02)
    slippage_rate: float = Field(default=0.0005, ge=0, le=0.02)

@router.post('/plan')
async def strategy_plan(payload: PlanInput):
    cfg = RotationConfig(payload.target_net_pct, payload.max_loss_pct, payload.fee_rate, payload.slippage_rate)
    return build_plan(payload.closes, cfg).to_dict()

@router.post('/position')
async def position_plan(payload: PositionInput):
    cfg = RotationConfig(payload.target_net_pct, payload.max_loss_pct, payload.fee_rate, payload.slippage_rate)
    return manage_position(payload.entry, payload.current, cfg).to_dict()
