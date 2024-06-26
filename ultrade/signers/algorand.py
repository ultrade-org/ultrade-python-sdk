from ultrade.utils.encode import normalize_address, determine_address_type
from .main import Signer
from algosdk import mnemonic, account, abi
from algosdk.logic import get_application_address
from algosdk.transaction import (
    PaymentTxn,
    AssetTransferTxn,
    ApplicationCallTxn,
    OnComplete,
    assign_group_id,
    wait_for_confirmation,
)
from algosdk.util import sign_bytes
from eth_utils import keccak
from ..types import WormholeChains, Technology


class AlgorandSigner(Signer):
    """
    Signer implementation for Algorand.
    """

    def __init__(self, private_key):
        super().__init__(wormhole_chain_id=WormholeChains.ALGORAND)
        self.__algo_private_key = mnemonic.to_private_key(private_key)
        self._provider_name = Technology.ALGORAND.value

    def sign_data(self, message: bytes) -> str:
        """
        Sign the message using Algorand mnemonic.
        """
        signature = sign_bytes(message, self.__algo_private_key)
        return signature

    async def _deposit(
        self, amount: int, token_address: str | int, config: dict
    ) -> str:
        """
        Deposit the amount of tokens to the Token Manager Contract

        Args:
            amount (int): The amount of tokens to deposit.
            token_address (str | int): The id of the token to deposit.
        """
        try:
            token_address = int(token_address)
        except ValueError:
            raise Exception("You must provide a valid Algorand asset id.")

        algod_client = config.get("algod_client", None)
        login_user = config.get("login_user", None)
        codex_app_id = config.get("codex_app_id", None)

        if algod_client is None:
            raise Exception("Algod client is not set.")
        if login_user is None:
            raise Exception("Login user is not set.")
        if codex_app_id is None:
            raise Exception("Codex app id is not set.")

        codex_address = get_application_address(codex_app_id)

        params = algod_client.suggested_params()
        method = abi.Method.from_signature("depositToCodex(byte[])uint64")
        selector = method.get_selector()

        login_address_hex = normalize_address(
            login_user.address,
            determine_address_type(login_user.wormhole_chain_id, False),
        ).hex()
        login_chain_id_hex = login_user.wormhole_chain_id.to_bytes(8, "big").hex()

        message = login_address_hex + login_chain_id_hex
        message_bytes = bytes.fromhex(message)
        box_name = (
            login_address_hex
            + login_chain_id_hex
            + token_address.to_bytes(32, "big").hex()
            + self.wormhole_chain_id.to_bytes(8, "big").hex()
        )
        box_name_bytes = bytes.fromhex(box_name)
        msg_args = method.args[0].type.encode(bytes(message_bytes))

        if token_address == 0:
            asset_transfer_txn = PaymentTxn(
                sender=self.address,
                sp=params,
                receiver=codex_address,
                amt=amount,
            )
        else:
            asset_transfer_txn = AssetTransferTxn(
                sender=self.address,
                sp=params,
                receiver=codex_address,
                amt=amount,
                index=token_address,
            )

        app_call_txn = ApplicationCallTxn(
            sender=self.address,
            app_args=[selector, msg_args],
            sp=params,
            index=codex_app_id,
            on_complete=OnComplete.NoOpOC,
            boxes=[[codex_app_id, keccak(box_name_bytes)]],
        )

        assign_group_id([asset_transfer_txn, app_call_txn])

        tx_id = algod_client.send_transactions(
            [
                asset_transfer_txn.sign(self.__algo_private_key),
                app_call_txn.sign(self.__algo_private_key),
            ]
        )
        result = wait_for_confirmation(algod_client, tx_id, 4)
        if not result:
            raise Exception("Deposit failed.")

    @property
    def address(self) -> str:
        """
        Get the Algorand address corresponding to the mnemonic.
        """
        return account.address_from_private_key(self.__algo_private_key)
