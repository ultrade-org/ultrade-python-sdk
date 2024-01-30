import pytest
from ultrade.sdk_client import Client
from ultrade import Signer
from .test_credentials import TEST_API_URL, TEST_MNEMONIC_KEY, TEST_SOCKET_URL, TEST_ETH_PRIVATE_KEY
import pytest_asyncio


@pytest_asyncio.fixture
async def client():
    login_user = Signer.create_signer(TEST_ETH_PRIVATE_KEY)
    client_instance = Client(network="testnet", api_url=TEST_API_URL, websocket_url=TEST_SOCKET_URL)
    await client_instance.set_login_user(login_user)
    return client_instance