from abc import ABC, abstractmethod
from .private_key import PrivateKey
from ..types import KeyType, WormholeChains

class Signer(ABC):
  """
  Abstract base class for signers.
  """
  def __init__(self, private_key, wormhole_chain_id: int = WormholeChains.UNSET):
    self.private_key = private_key
    self.wormhole_chain_id = wormhole_chain_id

  @abstractmethod
  def sign_data(self, message: bytes) -> str:
    pass

  @abstractmethod
  def get_address(self) -> str:
    pass
  
  def get_provider_name(self) -> str:
    if self.get_provider_name is None:
      raise Exception("Provider name is not set.")
    return self.provider_name

  def get_wormhole_chain_id(self) -> WormholeChains:
    """
    Get the wormhole chain id.

    Args:
      chain_id (int): The chain id.

    Returns:
      int: The chain id.
    """
    if self.wormhole_chain_id == WormholeChains.UNSET:
      raise Exception("Chain id is not set.")
    return self.wormhole_chain_id

class SignerFactory:
  """
  Factory class for creating signers based on the private key type.
  """

  @staticmethod
  def create_signer(private_key: str) -> Signer:
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

    _private_key = PrivateKey(private_key)

    if _private_key.key_type == KeyType.ALGORAND:
      from .algorand import AlgorandSigner
      return AlgorandSigner(private_key)
    elif _private_key.key_type == KeyType.ETH:
      from .ethereum import EthereumSigner
      return EthereumSigner(private_key)
    else:
      raise Exception("Invalid private key or mnemonic.")
    