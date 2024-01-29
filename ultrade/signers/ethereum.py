from ultrade.encode import determine_address_type, normalize_address
from .main import Signer
from web3 import Web3, HTTPProvider
from web3.middleware import geth_poa_middleware
from eth_account import Account
from eth_keys import keys
from eth_account.messages import encode_defunct
from ..types import Providers, WormholeChains

GAS_LIMIT = 1000000


class EthereumSigner(Signer):
    """
    Signer implementation for EVM chains.
    """

    def __init__(self, private_key):
        # TODO: add login from ETHEREUM instead of Polygon
        super().__init__(wormhole_chain_id=WormholeChains.POLYGON)
        self.__eth_private_key = keys.PrivateKey(bytes.fromhex(private_key))
        self.__private_key = private_key
        self._provider_name = Providers.METAMASK.value

    def sign_data(self, message: bytes) -> str:
        """
        Sign the message using Ethereum.
        """
        signed_data = Account.sign_message(
            encode_defunct(message), self.__eth_private_key
        )
        return signed_data.signature

    async def _deposit(
        self, amount: int, token_address: str | int, config: dict
    ) -> str:
        """
        Deposit the amount of tokens to the Token Manager Contract

        Args:
            amount (int): The amount of tokens to deposit.
            token_address (str | int): The id of the token to deposit.
        """
        is_valid_token = Web3.is_address(token_address)
        if not is_valid_token:
            raise Exception("You must provide a valid EVM token address.")

        rpc_url = config.get("rpc_url", None)
        tmc_configs = config.get("tmc_configs", None)
        login_user = config.get("login_user", None)

        login_address = normalize_address(
            login_user.address,
            determine_address_type(login_user.wormhole_chain_id, False),
        )

        if tmc_configs is None:
            raise Exception("Token Manager Contract configs are not set.")
        if rpc_url is None:
            raise Exception("RPC URL is not set. Please provide a valid RPC URL.")

        web3 = Web3(HTTPProvider(rpc_url))
        web3.middleware_onion.inject(geth_poa_middleware, layer=0)

        if not web3.is_connected():
            raise Exception(
                "Failed to connect to the Ethereum RPC URL. Please check your connection."
            )

        chain_id = web3.eth.chain_id
        tmc_config = [obj for obj in tmc_configs if obj["chainId"] == str(chain_id)]
        if tmc_config:
            tmc_config = tmc_config[0]
        else:
            raise Exception(
                f"Chain ID {chain_id} is not supported by the Token Manager Contract. Please specify rpc_url for supported chain IDs."
            )

        abi = [
            {
                "inputs": [
                    {"internalType": "address", "name": "token", "type": "address"},
                    {"internalType": "uint256", "name": "amount", "type": "uint256"},
                    {"internalType": "bytes", "name": "loginAddress", "type": "bytes"},
                    {
                        "internalType": "uint256",
                        "name": "loginChainId",
                        "type": "uint256",
                    },
                ],
                "name": "depositToCodex",
                "outputs": [
                    {"internalType": "uint64", "name": "sequence", "type": "uint64"}
                ],
                "stateMutability": "nonpayable",
                "type": "function",
            }
        ]

        tmc_address = tmc_config["tmc"]
        tmc_contract = web3.eth.contract(address=Web3.to_checksum_address(tmc_address), abi=abi)
        

        transaction = tmc_contract.functions.depositToCodex(
            token_address,
            amount,
            login_address,
            login_user.wormhole_chain_id,
        ).build_transaction(
            {
                "from": self.address,
                "gas": GAS_LIMIT * 10,
                "gasPrice": web3.to_wei("50", "gwei"),
                "nonce": web3.eth.get_transaction_count(self.address),
            }
        )

        signed_txn = web3.eth.account.sign_transaction(
            transaction, private_key=self.__private_key
        )
        tx_hash = web3.eth.send_raw_transaction(signed_txn.rawTransaction)
        tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)

        return tx_receipt.transactionHash.hex()

    @property
    def address(self) -> str:
        """
        Get the Ethereum address corresponding to the private key.
        """
        return Account.from_key(self.__private_key).address
