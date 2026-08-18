import json

from backend.certification import step6_runner


def test_step6_runner_persists_pass(tmp_path, monkeypatch):
    monkeypatch.setattr(step6_runner, "AUDIT_DIR", tmp_path)
    monkeypatch.setattr(step6_runner, "AUDIT_FILE", tmp_path / "validation.jsonl")
    monkeypatch.setattr(step6_runner, "CERT_FILE", tmp_path / "certification.json")

    result = step6_runner.run(mode="paper", bars=10_000)

    assert result["status"] == "PASS"
    assert (tmp_path / "validation.jsonl").exists()
    cert = json.loads((tmp_path / "certification.json").read_text())
    assert cert["status"] == "PASS"
    assert {g["name"] for g in cert["gates"]} == {
        "deterministic_backtest",
        "finite_metrics",
        "drawdown_bounded",
        "cost_accounting",
        "performance",
    }
