from abc import ABC, abstractmethod
from .private_key import PrivateKey
from ..types import KeyType, WormholeChains


class Signer(ABC):
    """
    Abstract base class for signers.
    """

    def __init__(self, wormhole_chain_id: int = WormholeChains.UNSET):
        self._wormhole_chain_id = wormhole_chain_id

    @classmethod
    def create_signer(cls, private_key: str) -> "Signer":
        """
        Creates a signer based on the private key type.

        Args:
          private_key (str): The private eth key or algorand mnemonic.
          wormhole_chain_id (int): Id that identifies the chain in wormhole bridge.

        Returns:
          Signer: An instance of the appropriate signer based on the wormhole id.

        Raises:
          Exception: If the private key or mnemonic is invalid.
        """

        key = PrivateKey(private_key)

        if key.key_type == KeyType.ALGORAND:
            from .algorand import AlgorandSigner

            return AlgorandSigner(private_key)
        elif key.key_type == KeyType.ETH:
            from .ethereum import EthereumSigner

            return EthereumSigner(private_key)
        else:
            raise Exception("Invalid private key or mnemonic.")

    @abstractmethod
    def sign_data(self, message: bytes) -> str:
        raise NotImplementedError("This method should be implemented by subclasses.")

    @property
    @abstractmethod
    def address(self) -> str:
        raise NotImplementedError("This method should be implemented by subclasses.")

    @abstractmethod
    def _deposit(self, amount: int, token_address: str | int, config: dict) -> str:
        raise NotImplementedError("This method should be implemented by subclasses.")

    @property
    def provider_name(self) -> str:
        if self._provider_name is None:
            raise Exception("Provider name is not set.")
        return self._provider_name

    @property
    def wormhole_chain_id(self) -> WormholeChains:
        """
        Get the wormhole chain id.

        Args:
          chain_id (int): The chain id.

        Returns:
          int: The chain id.
        """
        if self._wormhole_chain_id == WormholeChains.UNSET:
            raise Exception("Chain id is not set.")
        return self._wormhole_chain_id.value
