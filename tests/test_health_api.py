from fastapi.testclient import TestClient

from backend.main import app


def test_health_endpoint_is_fail_closed_and_well_formed():
    client = TestClient(app)
    response = client.get('/health')
    assert response.status_code == 200
    body = response.json()
    assert body['status'] == 'ok'
    assert body['version'] == '1.6.0'
    assert body['fail_closed'] is True
    assert body['live_trading'] is False


def test_health_never_reports_live_trading_by_default():
    client = TestClient(app)
    body = client.get('/health').json()
    assert body['live_trading'] is False
