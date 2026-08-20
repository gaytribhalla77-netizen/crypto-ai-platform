from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr

from auth.dependencies import CurrentUser, get_current_user
from security.authorized_web_auditor import AuthorizedWebAuditor, AuthorizationError, TargetSafetyError, send_disclosure_email

router = APIRouter(prefix="/api/security-audit", tags=["security-audit"])
_auditor = AuthorizedWebAuditor()


class AuditRequest(BaseModel):
    target: str
    authorization: str


class DisclosureRequest(BaseModel):
    recipient: EmailStr
    report: dict
    authorization: str


@router.post("/scan")
async def scan_target(payload: AuditRequest, user: CurrentUser = Depends(get_current_user)):
    """Run a non-destructive audit only after explicit target authorization."""
    try:
        return await _auditor.scan(payload.target, payload.authorization)
    except AuthorizationError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except TargetSafetyError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Target could not be audited safely: {type(exc).__name__}") from exc


@router.post("/disclose")
async def disclose(payload: DisclosureRequest, user: CurrentUser = Depends(get_current_user)):
    """Send a responsible-disclosure report through configured SMTP.

    The caller must explicitly authorize the disclosure action. The endpoint
    never discovers or guesses recipients and never sends without a recipient
    supplied by the operator.
    """
    if payload.authorization.strip().lower() != "i-authorize-this-disclosure":
        raise HTTPException(status_code=403, detail="Explicit disclosure authorization is required.")
    try:
        send_disclosure_email(payload.report, str(payload.recipient))
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {"sent": True, "recipient": str(payload.recipient)}
