import unittest
import json
import asyncio
from unittest.mock import MagicMock

from requests import patch
from ultrade.sdk_client import Client
from ultrade.signers.main import SignerFactory
from ultrade.types import ClientOptions
from .test_credentials import TEST_MNEMONIC_KEY, TEST_MAINNET_ALGOD_ADDRESS, TEST_ALGOD_TOKEN, TEST_ETH_PRIVATE_KEY
from algosdk.v2client import algod

class TestClient(unittest.TestCase):

    def setUp(self):
        self.algod_client = algod.AlgodClient(TEST_ALGOD_TOKEN, TEST_MAINNET_ALGOD_ADDRESS)
        self.algo_signer = SignerFactory.create_signer(TEST_MNEMONIC_KEY)
        self.eth_signer = SignerFactory.create_signer(TEST_ETH_PRIVATE_KEY)

    def test_configure_with_invalid_network(self):
        options: ClientOptions = {
            "algo_sdk_client": self.algod_client
        }
        with self.assertRaises(ValueError) as context:
            Client(network="testnet", **options)

        expected_error_message = "Network of the AlgodClient should be the same as the network specified in the options"
        self.assertEqual(str(context.exception), expected_error_message)
    
    def test_login_eth(self):
        options = ClientOptions()
        options["api_url"] = 'https://api.testnet.ultrade.org'
        client = Client(network="testnet", **options)

        loop = asyncio.get_event_loop()
        loop.run_until_complete(client.set_login_user(self.eth_signer))
        self.assertEqual(True, client.is_logged_in())

    def test_login_algorand(self):
        options = ClientOptions()
        options["api_url"] = 'https://api.testnet.ultrade.org'
        client = Client(network="testnet", **options)

        loop = asyncio.get_event_loop()
        loop.run_until_complete(client.set_login_user(self.algo_signer))
        self.assertEqual(True, client.is_logged_in())
    
    def _run_async(self, async_func):
        return asyncio.run(async_func)

if __name__ == "__main__":
    unittest.main()