import pytest

from backend.security.authorized_web_auditor import AuthorizedWebAuditor, AuthorizationError, TargetSafetyError
from backend.voice.service import VoiceService


@pytest.mark.asyncio
async def test_scan_requires_explicit_authorization():
    with pytest.raises(AuthorizationError):
        await AuthorizedWebAuditor().scan("https://example.com", "")


@pytest.mark.asyncio
async def test_private_targets_are_blocked():
    with pytest.raises(TargetSafetyError):
        await AuthorizedWebAuditor().scan("http://127.0.0.1:8000", "i-authorize-this-security-test")


@pytest.mark.asyncio
async def test_voice_recognizes_security_audit_without_side_effects():
    result = await VoiceService().handle("website security audit karo")
    assert result["intent"] == "security_audit"
    assert result["requires_authorization"] is True
    assert result["requires_confirmation"] is True
