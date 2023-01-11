from typing import Any, Dict, List, Optional, TypedDict

from . import api
from . import socket_client
from .algod_service import AlgodService
from .utils import is_asset_opted_in, is_app_opted_in, construct_args_for_app_call
from .constants import OPEN_ORDER_STATUS
from . import socket_options
from algosdk.v2client.algod import AlgodClient

OPTIONS = socket_options


class Order(TypedDict):
    id: str
    symbol: str
    side: str
    type: str
    time_force: str
    quantity: int
    price: int
    status: int


class NewOrderOptions(TypedDict):
    symbol: str
    side: str
    type: str
    quantity: int
    price: int


class AccountCredentials(TypedDict):
    mnemonic: str


class ClientOptions(TypedDict):
    network: str
    algo_sdk_client: AlgodClient
    api_url: str
    websocket_url: str


class Client ():
    """
    UltradeSdk client class. Handles subscribe/unsubscribe to ultrade websockets,
    also can create/cancel orders on the ultrade exchange

    Args:
        credentials (dict)

        options (dict) 

    """

    def __init__(self,
                 auth_credentials: AccountCredentials,
                 options: ClientOptions
                 ):
        if options["network"] == "mainnet":
            self.server = ''
            self.api_url = ""
        elif options["network"] == "testnet":
            self.api_url = "https://dev-apigw.ultradedev.net"
            self.server = 'https://node.testnet.algoexplorerapi.io'
        else:
            self.api_url = "http://localhost:5001"
            self.server = 'http://localhost:4001'

        if options["api_url"] != None:
            self.api_url = options["api_url"]

        self.client = AlgodService(options.get(
            "algo_sdk_client"), auth_credentials.get("mnemonic"))

        self.websocket_url: Optional[str] = options.get("websocket_url")
        self.mnemonic: Optional[str] = auth_credentials.get(
            "mnemonic")  # todo remove creds from here
        self.signer: Optional[Dict] = auth_credentials.get("signer")
        self.client_secret: Optional[str] = auth_credentials.get(
            "client_secret")
        self.company: Optional[str] = auth_credentials.get("company")
        self.client_id: Optional[str] = auth_credentials.get("client_id")

    async def new_order(self, symbol, side, type, quantity, price):
        """
        Create new order by sending group transaction to algorand API

        Return transaction id
        """
        partner_app_id = "87654321"  # temporary solution

        if not self.mnemonic:
            raise Exception(
                "You need to specify mnemonic or signer to execute this method")

        info = await api.get_exchange_info(symbol)

        sender_address = self.client.get_account_address()

        unsigned_txns = []
        account_info = self.get_balance_and_state(sender_address)

        if is_asset_opted_in(account_info.get("balances"), info["base_id"]) is False:
            unsigned_txns.append(self.client.opt_in_asset(
                sender_address, info["base_id"]))

        if is_asset_opted_in(account_info.get("balances"), info["price_id"]) is False:
            unsigned_txns.append(self.client.opt_in_asset(
                sender_address, info["price_id"]))

        if is_app_opted_in(info["application_id"], account_info.get("local_state")) is False:
            unsigned_txns.append(self.client.opt_in_app(
                info["application_id"], sender_address))

        app_args = construct_args_for_app_call(
            side, type, price, quantity, partner_app_id)
        asset_index = info["base_id"] if side == "S" else info["price_id"]
        transfer_amount = await self.client.calculate_transfer_amount(
            info["application_id"], side, quantity)

        if not transfer_amount:
            pass
        elif asset_index == 0:
            unsigned_txns.append(self.client.make_payment_txn(
                info["application_id"], sender_address, transfer_amount))
        else:
            unsigned_txns.append(self.client.make_transfer_txn(
                asset_index, info["application_id"], sender_address, transfer_amount))

        unsigned_txns.append(self.client.make_app_call_txn(
            asset_index, app_args, info["application_id"]))

        signed_txns = self.client.sign_transaction_grp(unsigned_txns)
        tx_id = self.client.send_transaction_grp(signed_txns)

        print(f"Order created successfully, order_id: {tx_id}")
        return tx_id

    async def cancel_order(self, symbol: str, order_id: int):
        """
        Find an open order by provided id and symbol.
        If an order was found, it sends appCall transaction with cancel request to algorand API

        Return transaction id
        """
        if not self.mnemonic:
            raise Exception(
                "You need to specify mnemonic or signer to execute this method")

        order = await api.get_order_by_id(symbol, order_id)
        exchange_info = await api.get_exchange_info(symbol)

        app_args = ["cancel_order", order["orders_id"], order["slot"]]
        unsigned_txn = self.client.make_app_call_txn(
            exchange_info["price_id"], app_args, order["application_id"])

        signed_txn = self.client.sign_transaction_grp(unsigned_txn)
        tx_id = self.client.send_transaction_grp(signed_txn)
        return tx_id

    async def cancel_all_orders(self, symbol):
        """
        Perform cancellation of all existing orders for wallet specified in algod client
        by sending appCall transaction to algorand API

        Return transaction id
        """
        address = self.client.get_account_address()
        user_trade_orders = await api.get_address_orders(
            address, OPEN_ORDER_STATUS, symbol)
        exchange_info = await api.get_exchange_info(symbol)

        unsigned_txns = []
        for order in user_trade_orders:
            app_args = ["cancel_order", order["orders_id"], order["slot"]]
            unsigned_txn = self.client.make_app_call_txn(
                exchange_info["price_id"], app_args, order["pair_id"])
            unsigned_txns.append(unsigned_txn)

        if len(unsigned_txns) == 0:
            return None

        signed_txns = self.client.sign_transaction_grp(unsigned_txns)
        tx_id = self.client.send_transaction_grp(signed_txns)
        return tx_id

    def get_balance_and_state(self, address) -> Dict[str, int]:
        balances: Dict[str, int] = dict()

        account_info = self.client.get_account_info(address)

        balances[0] = account_info["amount"]

        assets: List[Dict[str, Any]] = account_info.get("assets", [])
        for asset in assets:
            asset_id = asset["asset-id"]
            amount = asset["amount"]
            balances[asset_id] = amount

        return {"balances": balances, "local_state": account_info.get('apps-local-state', [])}

    async def subscribe(self, options, callback):
        """
        Subscribe current client to websocket streams listed in arg "options"

        Return id of established connection
        """
        if options.get("address") == None:
            options["address"] = self.client.get_account_address()
        return await socket_client.subscribe(self.websocket_url, options, callback)

    async def unsubscribe(self, connection_id):
        """
        Unsubscribe from ws connection by provided id
        """
        await socket_client.unsubscribe(connection_id)
