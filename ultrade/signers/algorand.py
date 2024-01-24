from .main import Signer
from algosdk import mnemonic, account
from algosdk.util import sign_bytes
from ..types import WormholeChains, Providers

class AlgorandSigner(Signer):
    """
    Signer implementation for Algorand.
    """

    def __init__(self, private_key):
        super().__init__(wormhole_chain_id=WormholeChains.ALGORAND)
        self.__algo_private_key = mnemonic.to_private_key(private_key)
        self._provider_name = Providers.MYALGO.value

    def sign_data(self, message: bytes) -> str:
        """
        Sign the message using Algorand mnemonic.
        """
        signature = sign_bytes(message, self.__algo_private_key)
        return signature
    
    @property
    def address(self) -> str:
        """
        Get the Algorand address corresponding to the mnemonic.
        """
        return account.address_from_private_key(self.__algo_private_key)
