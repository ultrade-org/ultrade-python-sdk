import unittest
from ultrade.signers.main import Signer
from ultrade.signers.algorand import AlgorandSigner
from ultrade.signers.ethereum import EthereumSigner
from tests.test_credentials import (
    TEST_MNEMONIC_KEY,
    TEST_ETH_PRIVATE_KEY,
    TEST_MESSAGE_TO_SIGN,
)
from eth_account import Account
from eth_account.messages import encode_defunct
from eth_keys import keys
from algosdk.util import sign_bytes, verify_bytes
from algosdk import mnemonic, account


class TestCreateSigner(unittest.TestCase):
    def test_create_algorand_signer(self):
        private_key = TEST_MNEMONIC_KEY
        signer = Signer.create_signer(private_key)
        self.assertIsInstance(signer, AlgorandSigner)

    def test_create_ethereum_signer(self):
        private_key = TEST_ETH_PRIVATE_KEY
        signer = Signer.create_signer(private_key)
        self.assertIsInstance(signer, EthereumSigner)

    def test_invalid_private_key(self):
        private_key = "INVALID_PRIVATE_KEY"
        with self.assertRaises(Exception):
            Signer.create_signer(private_key)


class TestSignMessage(unittest.TestCase):
    def setUp(self):
        self.ethereum_signer = Signer.create_signer(TEST_ETH_PRIVATE_KEY)
        self.algorand_signer = Signer.create_signer(TEST_MNEMONIC_KEY)

    def test_eth_sign_data(self):
        message = bytes(TEST_MESSAGE_TO_SIGN, "utf-8")
        encoded_message = encode_defunct(message)
        eth_private_key = keys.PrivateKey(bytes.fromhex(TEST_ETH_PRIVATE_KEY))

        expected_signature = Account.sign_message(
            encoded_message, eth_private_key
        ).signature
        signature = self.ethereum_signer.sign_data(message)

        expected_address = Account.from_key(TEST_ETH_PRIVATE_KEY).address
        recovered_address = Account.recover_message(
            encoded_message, signature=signature
        )

        self.assertEqual(recovered_address, expected_address)
        self.assertEqual(signature, expected_signature)
        self.assertEqual(expected_address, self.ethereum_signer.address)

    def test_algorand_sign_data(self):
        message = bytes(TEST_MESSAGE_TO_SIGN, "utf-8")
        algo_private_key = mnemonic.to_private_key(TEST_MNEMONIC_KEY)

        expected_signature = sign_bytes(message, algo_private_key)
        signature = self.algorand_signer.sign_data(message)

        public_key = account.address_from_private_key(algo_private_key)
        is_valid = verify_bytes(message, signature, public_key)

        self.assertTrue(is_valid)
        self.assertEqual(signature, expected_signature)
        self.assertEqual(public_key, self.algorand_signer.address)


if __name__ == "__main__":
    unittest.main()
