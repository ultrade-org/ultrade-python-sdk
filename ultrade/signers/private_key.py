from eth_keys import keys
from bip_utils import AlgorandMnemonicValidator
from eth_utils import is_hex
from ..types import KeyType


class InvalidKeyError(Exception):
    pass


class PrivateKey:
    def __init__(self, key_str: str):
        self.key_str = key_str
        self.key_type = self.determine_key_type()

    def determine_key_type(self) -> KeyType:
        if self.is_valid_ethereum_private_key():
            return KeyType.ETH
        elif self.is_valid_algo_mnemonic():
            return KeyType.ALGORAND
        else:
            raise InvalidKeyError("Invalid private key or mnemonic.")

    def is_valid_ethereum_private_key(self) -> bool:
        key = self.key_str
        if not is_hex(key) or len(key) != 64:
            return False
        try:
            keys.PrivateKey(bytes.fromhex(key))
            return True
        except (ValueError, TypeError):
            return False

    def is_valid_algo_mnemonic(self) -> bool:
        return AlgorandMnemonicValidator().IsValid(self.key_str)
