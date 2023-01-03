from random import random
from typing import Any, Dict, List, Optional, Tuple, Union

from algosdk import encoding
import api
from algod_service import AlgodService
import utils
import base64
import msgpack

from decode import unpack_data
from constants import OPEN_ORDER_STATUS, BALANCE_DECODE_FORMAT

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

    def new_order(self, symbol, order):
        # todo: implement use of on_complete callback, figure out where to get "transfer_amount"
        if not self.mnemonic:
            raise "You need to specify mnemonic or signer to execute this method"
        self.client.validate_transaction_order()

        info = api.get_exchange_info(symbol)

        sender_address = self.client.get_account_address()

        unsigned_txns = []
        account_info = self.get_balance_and_state(sender_address)

        if utils.is_asset_opted_in(account_info.get("balances"), info["base_id"]) is False:
            unsigned_txns.append(self.client.opt_in_asset(
                sender_address, info["base_id"]))

        if utils.is_asset_opted_in(account_info.get("balances"), info["price_id"]) is False:
            unsigned_txns.append(self.client.opt_in_asset(
                sender_address, info["price_id"]))

        if utils.is_app_opted_in(info["application_id"], account_info.get("local_state")) is False:
            unsigned_txns.append(self.client.opt_in_app(
                info["application_id"], sender_address))

        app_args = utils.construct_args_for_app_call(
            order["side"], order["type"], order["price"], order["quantity"], order["partner_app_id"])
        asset_index = info["base_id"] if order["side"] == "S" else info["price_id"]

        if asset_index == 0:
            unsigned_txns.append(self.client.make_payment_txn(
                info["application_id"], sender_address, order["transfer_amount"]))
        else:
            unsigned_txns.append(self.client.make_transfer_txn(
                asset_index, info["application_id"], sender_address, order["transfer_amount"]))

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
        unsigned_txn = self.client.make_app_call_txn(asset_index, app_args, order["application_id"])

        signed_txn = self.client.sign_transaction_grp(unsigned_txn)
        tx_id = self.client.send_transaction_grp(signed_txn)

    
    def cancel_all_orders(self, symbol):   
        address = self.client.get_account_address()
        user_trade_orders = api.get_trade_orders(address, OPEN_ORDER_STATUS, symbol)
        asset_index = api.get_exchange_info(symbol)["price_id"]

        unsigned_txns = []
        i = 0
        for order in user_trade_orders:
            i=i+1
            print(i)
            app_args = ["cancel_order", order["orders_id"], order["slot"]]
            print("asset_index",asset_index)
            unsigned_txn = self.client.make_app_call_txn(asset_index, app_args, order["pair_id"]) 
            unsigned_txns.append(unsigned_txn)

        signed_txns = self.client.sign_transaction_grp(unsigned_txns)
        tx_id = self.client.send_transaction_grp(signed_txns)

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

    def subscribe(self):
        pass

    def unsubscribe(self):
        pass

    def connect():
        pass

    def get_pair_balance(self, app_id):
        address = self.client.get_account_address()
        encoded_data = api.get_encoded_balance(address, app_id)
        balance_data = unpack_data(encoded_data, BALANCE_DECODE_FORMAT)

        return balance_data