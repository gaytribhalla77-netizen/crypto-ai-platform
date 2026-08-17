import os, time
os.environ.setdefault('JWT_SECRET_KEY','unit-test-secret-please-change-1234567890')
from security.totp import new_secret, code, verify
from security.vault import CredentialVault

def test_totp_roundtrip():
    s=new_secret(); c=code(s); assert len(c)==6 and verify(s,c)

def test_vault_roundtrip():
    v=CredentialVault(); payload={'api_key':'secret','api_secret':'secret2'}
    enc=v.encrypt(payload); assert 'secret' not in enc; assert v.decrypt(enc)==payload
