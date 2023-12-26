from .main import Signer
from eth_account import Account
from eth_keys import keys
from eth_account.messages import encode_defunct
from ..types import Providers, WormholeChains

class EthereumSigner(Signer):
    """
    Signer implementation for EVM chains.
    """

    def __init__(self, private_key):
        #TODO: add login from ETHEREUM instead of Polygon
        super().__init__(wormhole_chain_id=WormholeChains.POLYGON)
        self.__eth_private_key = keys.PrivateKey(bytes.fromhex(private_key))
        self.__private_key = private_key
        self._provider_name = Providers.METAMASK.value

    def sign_data(self, message: bytes) -> str:
        """
        Sign the message using Ethereum.
        """
        signed_data = Account.sign_message(encode_defunct(message), self.__eth_private_key)
        return signed_data.signature
    
    @property
    def address(self) -> str:
        """
        Get the Ethereum address corresponding to the private key.
        """
        return Account.from_key(self.__private_key).address
    