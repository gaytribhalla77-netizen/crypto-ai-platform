import pytest
from backend.exchanges.binance.testnet_client import BinanceTestnetClient


def test_missing_credentials_fail_closed_before_network():
    client = BinanceTestnetClient(api_key="", api_secret="")
    with pytest.raises(RuntimeError, match="credentials are missing"):
        client._signed({"recvWindow": 5000})


def test_testnet_base_is_not_live():
    assert BinanceTestnetClient.BASE == "https://testnet.binance.vision"
