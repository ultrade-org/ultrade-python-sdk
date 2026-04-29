import pytest
import pytest_asyncio
from ultrade import Client, Signer

# Credentials live in tests/test_credentials.py (gitignored). When missing,
# the `client` / `trading_client` fixtures skip the test instead of erroring at
# collection time so the env-driven suites (e.g. dev4_test.py) still run.
try:
    from .test_credentials import (
        TEST_API_URL,
        TEST_SOCKET_URL,
        TEST_ETH_PRIVATE_KEY,
        TRADING_KEY,
        TRADING_KEY_MNEMONIC,
        TRADING_KEY_ADDRESS,
    )
    _CREDS_AVAILABLE = True
except ImportError:
    _CREDS_AVAILABLE = False


@pytest_asyncio.fixture
async def client():
    if not _CREDS_AVAILABLE:
        pytest.skip("tests/test_credentials.py not configured")
    login_user = Signer.create_signer(TEST_ETH_PRIVATE_KEY)
    client_instance = Client(
        network="testnet", api_url=TEST_API_URL, websocket_url=TEST_SOCKET_URL
    )
    await client_instance.set_login_user(login_user)
    return client_instance


@pytest_asyncio.fixture
async def trading_client():
    if not _CREDS_AVAILABLE:
        pytest.skip("tests/test_credentials.py not configured")
    client_instance = Client(
        network="testnet", api_url=TEST_API_URL, websocket_url=TEST_SOCKET_URL
    )
    client_instance.set_trading_key(
        trading_key=TRADING_KEY,
        address=TRADING_KEY_ADDRESS,
        trading_key_mnemonic=TRADING_KEY_MNEMONIC,
    )
    return client_instance
