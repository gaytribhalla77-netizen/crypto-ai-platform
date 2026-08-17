import base64, json, os
from cryptography.fernet import Fernet
from sqlalchemy import select
from database.models import CredentialVault as CredentialVaultModel
from core.config import settings

class CredentialVault:
    """Encrypts credentials at rest. Explicit env key wins; otherwise derives
    a stable Fernet key from the application's strong JWT secret."""
    def __init__(self):
        raw = os.getenv('CREDENTIAL_VAULT_KEY','').strip()
        if raw:
            key=raw.encode()
        else:
            import hashlib
            key=base64.urlsafe_b64encode(hashlib.sha256(settings.secret_key.encode()).digest())
        try: self.f = Fernet(key)
        except Exception as e: raise RuntimeError('Invalid credential-vault key configuration.') from e
    def encrypt(self, payload: dict) -> str:
        return self.f.encrypt(json.dumps(payload, separators=(',',':')).encode()).decode()
    def decrypt(self, value: str) -> dict:
        return json.loads(self.f.decrypt(value.encode()).decode())

    async def get_provider_credentials(self, session, user_id: int, provider: str) -> dict:
        """Return the newest credential set for this authenticated user/provider.
        Environment credentials are intentionally not used here; callers that
        need a shared single-operator deployment must opt in explicitly.
        """
        result = await session.execute(
            select(CredentialVaultModel)
            .where(CredentialVaultModel.user_id == user_id,
                   CredentialVaultModel.provider == provider.strip().lower())
            .order_by(CredentialVaultModel.updated_at.desc(), CredentialVaultModel.id.desc())
        )
        row = result.scalars().first()
        if row is None:
            raise RuntimeError(f"{provider} credentials are not configured for this user.")
        return self.decrypt(row.encrypted_payload)
