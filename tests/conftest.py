import pytest
from ultrade.sdk_client import Client
from ultrade import Signer
from .test_credentials import TEST_API_URL, TEST_MNEMONIC_KEY
import pytest_asyncio


@pytest_asyncio.fixture
async def client_class_scope():
    login_user = Signer.create_signer(TEST_MNEMONIC_KEY)
    client_instance = Client(network="testnet", api_url=TEST_API_URL)
    await client_instance.set_login_user(login_user)
    api_instance = client_instance.create_api()
    return client_instance, api_instance

   
