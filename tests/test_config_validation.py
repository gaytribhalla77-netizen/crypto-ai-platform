import subprocess
import sys


def test_environment_validator_accepts_safe_defaults(monkeypatch):
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("LIVE_TRADING", "false")
    monkeypatch.setenv("PAPER_TRADING", "true")
    monkeypatch.setenv("ENABLE_WORKERS", "false")
    result = subprocess.run([sys.executable, "scripts/validate_env.py"], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr + result.stdout


def test_environment_validator_rejects_live_without_gate(monkeypatch):
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("LIVE_TRADING", "true")
    monkeypatch.setenv("ENABLE_WORKERS", "true")
    monkeypatch.setenv("BROKER", "binance")
    monkeypatch.delenv("LIVE_TRADING_CONFIRM", raising=False)
    result = subprocess.run([sys.executable, "scripts/validate_env.py"], capture_output=True, text=True)
    assert result.returncode != 0
