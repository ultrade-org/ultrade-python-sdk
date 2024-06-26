from ultrade.utils.encode import determine_address_type, normalize_address
from ultrade.types import Technology, WormholeChains
from ultrade.constants import TMC_ABI as abi, ERC20_ABI
from ultrade import Signer
from web3 import Web3, HTTPProvider
from web3.middleware import geth_poa_middleware
from eth_account import Account
from eth_keys import keys
from eth_account.messages import encode_defunct

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
        self._provider_name = Technology.EVM.value

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
        if not Web3.is_address(token_address):
            raise Exception("You must provide a valid EVM token address.")

        token_address = Web3.to_checksum_address(token_address)

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
        tmc_config = next(
            (obj for obj in tmc_configs if obj["chainId"] == str(chain_id)), None
        )
        if not tmc_config:
            raise Exception(
                f"Chain ID {chain_id} is not supported by the Token Manager Contract."
            )

        tmc_address = tmc_config["tmc"]
        if not Web3.is_address(tmc_address):
            raise Exception("Invalid Token Manager Contract address.")

        tmc_contract = web3.eth.contract(
            address=Web3.to_checksum_address(tmc_address), abi=abi
        )
        token_contract = web3.eth.contract(address=token_address, abi=ERC20_ABI)

        allowance = token_contract.functions.allowance(self.address, tmc_address).call()
        if allowance < amount:
            approve_txn = token_contract.functions.approve(
                tmc_address, amount
            ).build_transaction(
                {
                    "from": self.address,
                    "nonce": web3.eth.get_transaction_count(self.address),
                }
            )
            signed_approve_txn = web3.eth.account.sign_transaction(
                approve_txn, private_key=self.__private_key
            )
            web3.eth.send_raw_transaction(signed_approve_txn.rawTransaction)
            web3.eth.wait_for_transaction_receipt(signed_approve_txn.hash)

        transaction = tmc_contract.functions.depositToCodex(
            token_address,
            amount,
            login_address,
            login_user.wormhole_chain_id,
        ).build_transaction(
            {
                "from": self.address,
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
