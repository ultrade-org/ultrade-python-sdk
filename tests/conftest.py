from ultrade import Client, Signer
from .test_credentials import (
    TEST_API_URL,
    TEST_SOCKET_URL,
    TEST_ETH_PRIVATE_KEY,
    TRADING_KEY,
    TRADING_KEY_MNEMONIC,
    TRADING_KEY_ADDRESS,
)
import pytest_asyncio


@pytest_asyncio.fixture
async def client():
    login_user = Signer.create_signer(TEST_ETH_PRIVATE_KEY)
    client_instance = Client(
        network="testnet", api_url=TEST_API_URL, websocket_url=TEST_SOCKET_URL
    )
    await client_instance.set_login_user(login_user)
    return client_instance


@pytest_asyncio.fixture
async def trading_client():
    client_instance = Client(
        network="testnet", api_url=TEST_API_URL, websocket_url=TEST_SOCKET_URL
    )
    client_instance.set_trading_key(
        trading_key=TRADING_KEY,
        address=TRADING_KEY_ADDRESS,
        trading_key_mnemonic=TRADING_KEY_MNEMONIC,
    )
    return client_instance
