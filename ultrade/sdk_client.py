from typing import Any, Dict, List, Optional, TypedDict

from . import api
from . import socket_client
from .algod_service import AlgodService
from .utils import is_asset_opted_in, is_app_opted_in, construct_args_for_app_call
from .constants import OPEN_ORDER_STATUS


class Order(TypedDict):
    id: str
    symbol: str
    side: str
    type: str
    time_force: str
    quantity: int
    price: int
    status: int


class Client ():
    def __init__(self,
                 auth_credentials: Dict[str, Any],
                 options: Dict[str, Any]
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

    def new_order(self, order):
        if not self.mnemonic:
            raise "You need to specify mnemonic or signer to execute this method"
        self.client.validate_transaction_order()

        info = api.get_exchange_info(order["symbol"])

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
            order["side"], order["type"], order["price"], order["quantity"], order["partner_app_id"])
        asset_index = info["base_id"] if order["side"] == "S" else info["price_id"]
        transfer_amount = self.client.calculate_transfer_amount(
            info["application_id"], order["side"], order["quantity"])

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

    def cancel_order(self, symbol, order_id):
        if not self.mnemonic:
            raise "You need to specify mnemonic or signer to execute this method"
        self.client.validate_transaction_order()

        data = api.get_order_by_id(symbol, order_id)
        asset_index = api.get_exchange_info(symbol)["price_id"]
        order = data[0]

        app_args = ["cancel_order", order["orders_id"], order["slot"]]
        unsigned_txn = self.client.make_app_call_txn(
            asset_index, app_args, order["application_id"])

        signed_txn = self.client.sign_transaction_grp(unsigned_txn)
        tx_id = self.client.send_transaction_grp(signed_txn)
        return tx_id

    def cancel_all_orders(self, symbol):
        address = self.client.get_account_address()
        user_trade_orders = api.get_trade_orders(
            address, OPEN_ORDER_STATUS, symbol)
        asset_index = api.get_exchange_info(symbol)["price_id"]

        unsigned_txns = []
        for order in user_trade_orders:
            app_args = ["cancel_order", order["orders_id"], order["slot"]]
            unsigned_txn = self.client.make_app_call_txn(
                asset_index, app_args, order["pair_id"])
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

    def subscribe(self, options, callback):
        if options.get("address") == None:
            options["address"] = self.client.get_account_address()
        return socket_client.subscribe(self.websocket_url, options, callback)

    def unsubscribe(self, handler_id):
        socket_client.unsubscribe(handler_id)
