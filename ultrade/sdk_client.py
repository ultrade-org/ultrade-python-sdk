from typing import Any, Dict, List, Optional, TypedDict
import asyncio
import aiohttp
from algosdk.v2client.algod import AlgodClient
import time

from . import api
from .socket_client import SocketClient
from .algod_service import AlgodService
from .utils import is_asset_opted_in, is_app_opted_in, construct_new_order_args, construct_query_string_for_api_request, decode_txn_logs, validate_mnemonic
from .constants import OPEN_ORDER_STATUS, get_api_domain, set_domains, OrderType
from . import socket_options


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


class Client():
    """
    UltradeSdk client. Provides methods for creating and canceling orders on Ultrade exchange. Also can be used for subscribing to Ultrade data streams

    Args:
        auth_credentials (dict): credentials as a mnemonic or a private key
        options (dict): options allows to change default URLs for the API calls, also options should have algod client
    """

    def __init__(self,
                 auth_credentials: AccountCredentials,
                 options: ClientOptions
                 ):
        validate_mnemonic(auth_credentials.get(
            "mnemonic"))
        if options["network"] == "mainnet":
            self.algod_node = ''
            self.api_url = ""
        elif options["network"] == "testnet":
            self.api_url = "https://testnet-apigw.ultradedev.net"
            self.algod_node = 'https://node.testnet.algoexplorerapi.io'
            self.algod_indexer = 'https://indexer.testnet.algoexplorerapi.io'
        elif options["network"] == "dev":
            self.api_url = "https://dev-apigw.ultradedev.net"
            self.algod_node = 'https://node.testnet.algoexplorerapi.io'
            self.algod_indexer = 'https://indexer.testnet.algoexplorerapi.io'
        else:
            self.api_url = "http://localhost:5001"
            self.algod_node = 'http://localhost:4001'
            self.algod_indexer = 'http://localhost:8980'

        if options["api_url"] != None:
            self.api_url = options["api_url"]

        set_domains(self.api_url, self.algod_indexer, self.algod_node)

        self.socket_client = SocketClient(options.get("websocket_url", ""))
        self.client = AlgodService(options.get(
            "algo_sdk_client"), auth_credentials.get("mnemonic"))

        self.mnemonic: Optional[str] = auth_credentials.get(
            "mnemonic")  # todo remove creds from here
        self.signer: Optional[Dict] = auth_credentials.get("signer")
        self.client_secret: Optional[str] = auth_credentials.get(
            "client_secret")
        self.company: Optional[str] = auth_credentials.get("company")
        self.client_id: Optional[str] = auth_credentials.get("client_id")
        self.available_balance = {}
        self.pending_txns = {}
        self.algo_balance = None

    async def new_order(self, symbol, side, type, quantity, price, partner_app_id=0, direct_settle="N"):
        """
        Create new order on the Ultrade exchange by sending group transaction to algorand API

        Args:

            symbol (str): symbol represent existing pair, example: 'algo_usdt'
            side (str): represent either 'S' or 'B' order (SELL or BUY)
            type (str): can be one of these four order types: 'L', 'P', 'I' or 'M',
                which represent LIMIT, POST, IOC and MARKET orders respectively
            quantity (decimal): quantity of the base coin
            price (decimal): quantity of the price coin
            partner_app_id (int, default=0): id of the partner to use in transactions
            direct_settle (str): can be either "N" or "Y"

        If order successfully fulfilled returns dictionary with order_id and slot data in it

        """
        def sync_function():
            print(
                f"Preparing new order txn. symbol:{symbol}, side:{side}, quantity:{quantity}, price:{price}")

            if not self.mnemonic:
                raise Exception(
                    "You need to specify mnemonic or signer to execute this method")
            side_index = 0 if side == "B" else 1
            info = asyncio.run(api.get_exchange_info(symbol))
            account_info = self._get_balance_and_state()

            if self.pending_txns.get(symbol) == None:
                self.pending_txns[symbol] = {}

            self.pending_txns[symbol][side_index] = self.pending_txns[symbol].get(
                side_index, 0) + 1
            if self.available_balance.get(symbol) == None:
                self.available_balance[symbol] = [None, None]

            if self.pending_txns[symbol][side_index] == 1:
                self.algo_balance = account_info.get("balances", {"0": 0})["0"]
                self.available_balance[symbol][side_index] = asyncio.run(
                    self.client.get_available_balance(info["application_id"], side))
            elif self.available_balance[symbol][side_index] == None:
                wait_count = 0
                while (True):
                    if self.available_balance[symbol][side_index] != None:
                        break
                    if wait_count > 8:
                        raise Exception("Available_balance is None")
                    time.sleep(0.5)
                    wait_count += 0.5

            sender_address = self.client.get_account_address()
            min_algo_balance = asyncio.run(
                api.get_min_algo_balance(sender_address))
            unsigned_txns = []

            if is_asset_opted_in(account_info.get("balances"), info["base_id"]) is False:
                unsigned_txns.append(self.client.opt_in_asset(
                    sender_address, info["base_id"]))

            if is_asset_opted_in(account_info.get("balances"), info["price_id"]) is False:
                unsigned_txns.append(self.client.opt_in_asset(
                    sender_address, info["price_id"]))

            if is_app_opted_in(info["application_id"], account_info.get("local_state")) is False:
                unsigned_txns.append(self.client.opt_in_app(
                    info["application_id"], sender_address))

            app_args = construct_new_order_args(
                side, type, price, quantity, partner_app_id, direct_settle)
            asset_index = info["base_id"] if side == "S" else info["price_id"]

            transfer_amount = self.client.calculate_transfer_amount(
                side, quantity, price, info["base_decimal"], self.available_balance[symbol][side_index])

            if "algo" in symbol and (symbol.split("_")[0] == "algo" and side == "S" or symbol.split("_")[1] == "algo" and side == "B"):
                self.algo_balance -= transfer_amount
                print("algo/min_algo/t_amount",  self.algo_balance,
                      min_algo_balance, transfer_amount)
                if self.algo_balance < min_algo_balance:
                    self.algo_balance += transfer_amount
                    self.pending_txns[symbol][side_index] -= 1
                    if self.pending_txns[symbol][side_index] == 0:
                        self.available_balance[symbol][side_index] = None

                    raise Exception("Not enough algo for transfer")

            updatedQuantity = (
                quantity / 10**info["base_decimal"]) * price if side == "B" else quantity
            self.available_balance[symbol][side_index] = 0 if transfer_amount > 0 else self.available_balance[symbol][side_index] - updatedQuantity

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
            signed_app_call = signed_txns[-1]
            tx_id = signed_app_call.get_txid()
            self.client.send_transaction_grp(signed_txns)

            pending_txn = self.client.wait_for_transaction(tx_id)
            txn_logs = decode_txn_logs(
                pending_txn["logs"], OrderType.new_order)
            print(f"Order created successfully, order_id: {tx_id}")

            self.pending_txns[symbol][side_index] -= 1
            if self.pending_txns[symbol][side_index] == 0:
                self.available_balance[symbol][side_index] = None

            return txn_logs

        txn_logs = await asyncio.get_event_loop().run_in_executor(None, sync_function)
        return txn_logs

    async def cancel_order(self, symbol: str, order_id: int, slot: int):
        """
        Cancel the order matching the id and symbol arguments

        Args:
            symbol (str): symbol represent existing pair, example: 'algo_usdt'
            order_id (int): id of the order to cancel, can be provided by Ultrade API
            slot (int): order position in the smart contract

        Returns:
            str: First transaction id
        """
        def sync_function():
            print("Preparing cancel order txn")
            if not self.mnemonic:
                raise Exception(
                    "You need to specify mnemonic or signer to execute this method")

            exchange_info = asyncio.run(api.get_exchange_info(symbol))

            app_args = [OrderType.cancel_order, order_id, slot]
            unsigned_txn = self.client.make_app_call_txn(
                exchange_info["price_id"], app_args, exchange_info["application_id"])

            signed_txn = self.client.sign_transaction_grp(unsigned_txn)
            tx_id = self.client.send_transaction_grp(signed_txn)
            pending_txn = self.client.wait_for_transaction(tx_id)
            txn_logs = decode_txn_logs(
                pending_txn["logs"], OrderType.cancel_order)
            return txn_logs

        tx_id = await asyncio.get_event_loop().run_in_executor(None, sync_function)
        print(f"order {order_id} successfully canceled")
        return tx_id

    async def cancel_all_orders(self, symbol):
        """
        Perform cancellation of all existing orders for wallet specified in algod client

        Args:
            symbol (str): symbol represent existing pair, example: 'algo_usdt'

        Returns:
            str: First transaction id
        """
        user_trade_orders = await self.get_orders(symbol, OPEN_ORDER_STATUS)
        exchange_info = await api.get_exchange_info(symbol)

        unsigned_txns = []
        for order in user_trade_orders:
            app_args = [OrderType.cancel_order,
                        order["orders_id"], order["slot"]]
            unsigned_txn = self.client.make_app_call_txn(
                exchange_info["price_id"], app_args, order["pair_id"])
            unsigned_txns.append(unsigned_txn)

        if len(unsigned_txns) == 0:
            return None

        signed_txns = self.client.sign_transaction_grp(unsigned_txns)
        tx_id = self.client.send_transaction_grp(signed_txns)
        return tx_id

    def _get_balance_and_state(self) -> Dict[str, int]:
        balances: Dict[str, int] = dict()

        address = self.client.get_account_address()
        account_info = self.client.get_account_info(address)

        balances["0"] = account_info["amount"]

        assets: List[Dict[str, Any]] = account_info.get("assets", [])
        for asset in assets:
            asset_id = asset["asset-id"]
            amount = asset["amount"]
            balances[asset_id] = amount

        return {"balances": balances, "local_state": account_info.get('apps-local-state', [])}

    async def subscribe(self, options, callback):
        """
        Subscribe client to websocket streams listed in arg "options"
        Can be used multiple times for different pairs

        Args:
            options (dict): websocket subscribe options, example:
                {
                    'symbol': "yldy_stbl",
                    'streams': [OPTIONS.ORDERS, OPTIONS.TRADES],
                    'options': {"address": "your wallet address here"}
                }
            callback (function): a synchronous function, will be called on any occurred websocket event, should accept 'event' and 'args' parameters

        Returns:
            str: Id of the established connection
        """
        if options.get("address") == None:
            options["address"] = self.client.get_account_address()
        return await self.socket_client.subscribe(options, callback)

    async def unsubscribe(self, connection_id):
        """
        Unsubscribe from ws connection

        Args:
            connection_id (str): Id of the connection
        """
        await self.socket_client.unsubscribe(connection_id)

    async def get_orders(self, symbol=None, status=1, start_time=None, end_time=None, limit=500):
        """
        Get orders list for specified address
        With default status it return only open orders
        If symbol not specified, return orders for all pairs

        Args:
             symbol (str): symbol represents existing pair, example: 'algo_usdt'
             status (int): status of the returned orders

        Returns:
            list
        """
        address = self.client.get_account_address()
        query_string = construct_query_string_for_api_request(locals())

        session = aiohttp.ClientSession()
        url = f"{get_api_domain()}/market/orders-with-trades{query_string}"
        async with session.get(url) as resp:
            data = await resp.json()
            await session.close()
            return data

    async def get_wallet_transactions(self, symbol=None):
        """
        Get last transactions from current wallet, max_amount=100

        Args:
             symbol (str): symbol represents existing pair, example: 'algo_usdt'

        Returns:
            list
        """
        address = self.client.get_account_address()
        query_string = construct_query_string_for_api_request(locals())

        session = aiohttp.ClientSession()
        url = f"{get_api_domain()}/market/wallet-transactions{query_string}"
        async with session.get(url) as resp:
            data = await resp.json()
            await session.close()
            return data

    async def get_order_by_id(self, symbol, order_id):
        """
        Get order with specific id and symbol

        Returns:
            dict
        """
        # this endpoint should support symbol query
        # should work with user address
        session = aiohttp.ClientSession()
        url = f"{get_api_domain()}/market/getOrderById?orderId={order_id}"
        async with session.get(url) as resp:
            data = await resp.json()

            await session.close()
            try:
                order = data["order"][0]
                return order
            except TypeError:
                raise Exception("Order not found")

    async def get_balances(self, symbol):
        pair_info = await api.get_exchange_info(symbol)
        wallet_balances = self._get_balance_and_state()["balances"]
        address = self.client.get_account_address()
        min_algo = await api.get_min_algo_balance(address)

        exchange_balances = await self.client.get_pair_balances(
            pair_info["application_id"])

        balances_dict = {}

        balances_dict["priceCoin_locked"] = exchange_balances.get(
            "priceCoin_locked")
        balances_dict["priceCoin_available"] = exchange_balances.get(
            "priceCoin_available")
        balances_dict["baseCoin_locked"] = exchange_balances.get(
            "baseCoin_locked")
        balances_dict["baseCoin_available"] = exchange_balances.get(
            "baseCoin_available")

        for key in wallet_balances:
            if int(key) == pair_info["base_id"]:
                balances_dict["baseCoin"] = wallet_balances.get(
                    key) - min_algo if key == 0 else wallet_balances.get(key)
            if int(key) == pair_info["price_id"]:
                balances_dict["priceCoin"] = wallet_balances.get(
                    key) - min_algo if key == 0 else wallet_balances.get(key)
        return balances_dict
