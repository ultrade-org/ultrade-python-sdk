from typing import Any, Dict, List, Optional, TypedDict
import asyncio
import aiohttp
from algosdk.v2client.algod import AlgodClient
import time

from . import api
from .socket_client import SocketClient
from .algod_service import AlgodService
from .utils import is_asset_opted_in, is_app_opted_in, construct_new_order_args, \
    construct_query_string_for_api_request, decode_txn_logs, validate_mnemonic
from .constants import OPEN_ORDER_STATUS, BALANCE_DECODE_FORMAT, get_api_domain, set_domains, OrderType
from . import socket_options
from .decode import unpack_data

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
    UltradeSdk client. Provides methods for creating and canceling orders on Ultrade exchange.
    Also can be used for subscribing to Ultrade data streams

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
            self.api_url = "https://api.ultrade.org"
            self.algod_node = 'https://mainnet-api.algonode.cloud'
            self.algod_indexer = 'https://mainnet-idx.algonode.cloud'
            self.websocket_url = "wss://ws.mainnet.ultrade.org"
        elif options["network"] == "testnet":
            self.api_url = "https://api.testnet.ultrade.org"
            self.algod_node = 'https://testnet-api.algonode.cloud'
            self.algod_indexer = 'https://testnet-idx.algonode.cloud'
            self.websocket_url = "wss://ws.testnet.ultrade.org"
        else:
            raise Exception("Network could be either testnet or mainnet ")

        if options["api_url"] is not None:
            self.api_url = options["api_url"]

        set_domains(self.api_url, self.algod_indexer, self.algod_node)
        self.algod = options.get("algo_sdk_client", 0)
        self.socket_client = SocketClient(self.websocket_url)
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
        self.maintenance_mode_status = 0

    async def new_order(self, symbol, side, type, quantity, price, partner_app_id=0, direct_settle="N"):
        """
        Create new order on the Ultrade exchange by sending group transaction to algorand API

        Args:
            - symbol (str): The symbol representing an existing pair, for example: 'algo_usdt'
            - side (str): Represents either a 'S' or 'B' order (SELL or BUY).
            - type (str): Can be one of the following four order types: 'L', 'P', 'I', or 'M', which represent LIMIT,
              POST, IOC, and MARKET orders respectively.
            - quantity (decimal): The quantity of the base coin.
            - price (decimal): The quantity of the price coin.
            - partner_app_id (int, default=0): The ID of the partner to use in transactions.
            - direct_settle (str): Can be either "N" or "Y".

        Returns:
            A dictionary with the following keys:
            - 'order_id': The ID of the created order.
            - 'slot': The slot data of the created order.

        """
        def sync_function():
            self._check_maintenance_mode()
            if not self.mnemonic:
                raise Exception(
                    "You need to specify mnemonic or signer to execute this method")
            side_index = 0 if side == "B" else 1
            info = asyncio.run(api.get_exchange_info(symbol))
            account_info = self._get_balance_and_state()

            if self.pending_txns.get(symbol) is None:
                self.pending_txns[symbol] = {}

            self.pending_txns[symbol][side_index] = self.pending_txns[symbol].get(
                side_index, 0) + 1
            if self.available_balance.get(symbol) is None:
                self.available_balance[symbol] = [None, None]

            if self.pending_txns[symbol][side_index] == 1:
                self.algo_balance = account_info.get("balances", {"0": 0})["0"]
                self.available_balance[symbol][side_index] = asyncio.run(
                    self.client.get_available_balance(info["application_id"], side))
            elif self.available_balance[symbol][side_index] is None:
                wait_count = 0
                while (True):
                    if self.available_balance[symbol][side_index] is not None:
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

            if "algo" in symbol and (symbol.split("_")[0] == "algo"
                                     and side == "S" or symbol.split("_")[1] == "algo" and side == "B"):
                self.algo_balance -= transfer_amount

                if self.algo_balance < min_algo_balance:
                    self.algo_balance += transfer_amount
                    self.pending_txns[symbol][side_index] -= 1
                    if self.pending_txns[symbol][side_index] == 0:
                        self.available_balance[symbol][side_index] = None

                    raise Exception("Not enough algo for transfer")

            updatedQuantity = (
                quantity / 10**info["base_decimal"]) * price if side == "B" else quantity
            self.available_balance[symbol][side_index] = 0 if transfer_amount > 0 \
                else self.available_balance[symbol][side_index] - updatedQuantity

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

            self.pending_txns[symbol][side_index] -= 1
            if self.pending_txns[symbol][side_index] == 0:
                self.available_balance[symbol][side_index] = None

            return txn_logs

        txn_logs = await asyncio.get_event_loop().run_in_executor(None, sync_function)
        return txn_logs

    async def cancel_order(self, symbol: str, order_id: int, slot: int, fee=None):
        """
        Cancel the order matching the ID and symbol arguments.

        Args:
            - symbol (str): The symbol representing an existing pair, for example: 'algo_usdt'.
            - order_id (int): The ID of the order to cancel, which can be provided by the Ultrade API.
            - slot (int): The order position in the smart contract.
            - fee (int, default=None): The fee needed for canceling an order with direct settlement option enabled.

        Returns:
            The first transaction ID.
        """
        def sync_function():
            self._check_maintenance_mode()
            if not self.mnemonic:
                raise Exception(
                    "You need to specify mnemonic or signer to execute this method")

            user_trade_orders = asyncio.run(
                self.get_orders(symbol, OPEN_ORDER_STATUS))  # temporary, this function should use different order_id
            try:
                correct_order = [
                    order for order in user_trade_orders if order["orders_id"] == order_id][0]
            except Exception:
                # Ultrade connector in the hummingbot handles this exception
                raise Exception("Order not found")

            exchange_info = asyncio.run(api.get_exchange_info(symbol))

            foreign_asset_id = exchange_info["base_id"] if correct_order["order_side"] == 1 \
                else exchange_info["price_id"]
            app_args = [OrderType.cancel_order, order_id, slot]
            unsigned_txn = self.client.make_app_call_txn(
                foreign_asset_id, app_args, exchange_info["application_id"], fee)

            signed_txn = self.client.sign_transaction_grp(unsigned_txn)
            tx_id = self.client.send_transaction_grp(signed_txn)
            pending_txn = self.client.wait_for_transaction(tx_id)
            txn_logs = decode_txn_logs(
                pending_txn["logs"], OrderType.cancel_order)
            return txn_logs

        tx_id = await asyncio.get_event_loop().run_in_executor(None, sync_function)
        return tx_id

    async def cancel_all_orders(self, symbol, fee=None):
        """
        Perform cancellation of all existing orders for the wallet specified in the Algod client.

        Args:
            - symbol (str): The symbol representing an existing pair, for example: 'algo_usdt'.
            - fee (int, default=None): The fee needed for canceling orders with direct settlement option enabled.

        Returns:
            The first transaction ID.
        """
        self._check_maintenance_mode()
        user_trade_orders = await self.get_orders(symbol, OPEN_ORDER_STATUS)
        unique_ids = set()
        filtered_orders = []
        for order in user_trade_orders:
            if order['id'] not in unique_ids:
                unique_ids.add(order['id'])
                filtered_orders.append(order)

        exchange_info = await api.get_exchange_info(symbol)

        unsigned_txns = []
        for order in filtered_orders:
            foreign_asset_id = exchange_info["base_id"] if order["order_side"] == 1 else exchange_info["price_id"]

            app_args = [OrderType.cancel_order,
                        order["orders_id"], order["slot"]]
            unsigned_txn = self.client.make_app_call_txn(
                foreign_asset_id, app_args, order["pair_id"], fee)
            unsigned_txns.append(unsigned_txn)

        if len(unsigned_txns) == 0:
            return None

        signed_txns = self.client.sign_transaction_grp(unsigned_txns)
        tx_id = self.client.send_transaction_grp(signed_txns)
        return tx_id

    def _get_balance_and_state(self, account_info=None) -> Dict[str, int]:
        balances: Dict[str, int] = dict()

        if account_info is None:
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
        Subscribe the client to websocket streams for the specified options.

        Args:
            options (dict): A dictionary containing the websocket subscribe options, for example:
                {
                    'symbol': "yldy_stbl",
                    'streams': [OPTIONS.ORDERS, OPTIONS.TRADES],
                    'options': {"address": "your wallet address here"}
                }
            callback (function): A synchronous function that will be called on any occurred websocket event and should
            accept 'event' and 'args' parameters.

        Returns:
            str: The ID of the established connection.
        """

        def socket_callback(event, args):
            if event != "mode":
                return callback(event, args)

            if args != self.maintenance_mode_status:
                self.maintenance_mode_status = args

        if options.get("address") is None:
            options["address"] = self.client.get_account_address()

        if OPTIONS.MAINTENANCE not in options["streams"]:
            options["streams"].append(OPTIONS.MAINTENANCE)

        return await self.socket_client.subscribe(options, socket_callback)

    async def unsubscribe(self, connection_id):
        """
        Unsubscribe from a websocket connection.

        Args:
            connection_id (str): The ID of the connection to unsubscribe from.
        """
        await self.socket_client.unsubscribe(connection_id)

    async def get_orders(self, symbol=None, status=1, start_time=None, end_time=None, limit=500):
        """
        Get a list of orders for the specified address.

        With the default status, it will return only open orders.
        If no symbol is specified, it will return orders for all pairs.

        Args:
             symbol (str): The symbol representing an existing pair, for example: 'algo_usdt'.
             status (int): The status of the returned orders.

        Returns:
            list: A list of orders.
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
        Get the last transactions from the current wallet with a maximum amount of 100.

        Args:
             symbol (str): The symbol representing an existing pair, for example: 'algo_usdt'.

        Returns:
            list: A list of transactions.
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
        Get an order by the specified ID and symbol.

        Returns:
            dict: A dictionary containing the order information.
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
        """
        Returns a dictionary containing information about the assets stored in the wallet and exchange pair for
        a specified symbol. Return value contains the following keys:
            - 'priceCoin_available': The amount of price asset stored in the current pair and available for usage
            - 'baseCoin_locked': The amount of base asset locked in the current pair
            - 'baseCoin_available': The amount of base asset stored in the current pair and available for usage
            - 'baseCoin': The amount of base asset stored in the wallet
            - 'priceCoin': The amount of price asset stored in the wallet

        Args:
            symbol (str): The symbol representing an existing pair, for example: 'algo_usdt'

        Returns:
            dict

        """
        pair_info = await api.get_exchange_info(symbol)
        wallet_balances = self._get_balance_and_state()["balances"]
        address = self.client.get_account_address()

        min_algo = await api.get_min_algo_balance(address)
        exchange_balances = await self.client.get_pair_balances(
            pair_info["application_id"])

        balances_dict = {}

        balances_dict["priceCoin_locked"] = exchange_balances.get(
            "priceCoin_locked", 0)
        balances_dict["priceCoin_available"] = exchange_balances.get(
            "priceCoin_available", 0)
        balances_dict["baseCoin_locked"] = exchange_balances.get(
            "baseCoin_locked", 0)
        balances_dict["baseCoin_available"] = exchange_balances.get(
            "baseCoin_available", 0)

        for key in wallet_balances:
            if int(key) == pair_info["base_id"]:
                balances_dict["baseCoin"] = wallet_balances.get(
                    key) - min_algo if key == 0 else wallet_balances.get(key)
            if int(key) == pair_info["price_id"]:
                balances_dict["priceCoin"] = wallet_balances.get(
                    key) - min_algo if key == 0 else wallet_balances.get(key)
        return balances_dict

    async def get_account_balances(self, exchange_pair_list=None):
        """
        Returns a list of dictionaries containing information about the assets stored in the wallet and exchange pairs.
        Each dictionary includes the following keys:
            - 'free': the amount of the asset stored in the wallet.
            - 'total': the total amount of the asset, including any amounts stored in
            exchange pairs as available or locked balance.
            - 'asset': the name of the asset.
        The list contains one dictionary for each asset.

        Args:
            exchange_pair_list (dict[], default=None): list of pairs to get balances for,
                if not provided, would return balance for all currently available pairs.
                To get pairs that you want, use function "api.get_pair_list()".

        Returns:
            List of dictionaries
        """
        if exchange_pair_list is None:
            exchange_pair_list = await api.get_pair_list()

        address = self.client.get_account_address()
        acc_info = self.client.get_account_info(address)

        wallet_balances = self._get_balance_and_state(acc_info)["balances"]

        algo_buffer = 1000000
        min_algo = acc_info.get("min-balance", 0) + algo_buffer

        exchange_balances = await self._get_exchange_balances_from_account_info(acc_info)

        result_balances = {}

        for key in wallet_balances:
            asset_name = None
            filtered_pairs = list(filter(lambda pair: pair.get(
                "base_id", -1) == int(key) or pair.get("price_id", -1) == int(key), exchange_pair_list))

            total_asset_balance_from_pairs = 0
            for pair in filtered_pairs:
                pair_app_id = pair.get("application_id")

                exchange_pair = exchange_balances.get(
                    pair_app_id, {})

                is_asset_base_coin = int(pair["base_id"]) == int(key)

                if asset_name is None:
                    pair_name = pair.get("pair_name")
                    asset_name = pair_name.split(
                        "_")[0] if is_asset_base_coin else pair_name.split("_")[1]

                pair_asset_balance = exchange_pair.get(
                    "baseCoin_available", 0) + exchange_pair.get(
                    "baseCoin_locked", 0) if is_asset_base_coin else exchange_pair.get("priceCoin_available", 0) \
                    + exchange_pair.get("priceCoin_locked", 0)

                total_asset_balance_from_pairs = total_asset_balance_from_pairs + pair_asset_balance

            additional_fee = 0

            if key == "0":
                additional_fee = min_algo

            result_balances[key] = {"free": wallet_balances[key] - additional_fee,
                                    "total": total_asset_balance_from_pairs + wallet_balances[key] - additional_fee,
                                    "asset": asset_name}

        return result_balances

    async def _get_exchange_balances_from_account_info(self, acc_info):
        decoded_balances = {}
        local_state = acc_info.get("apps-local-state")
        for state in local_state:
            try:
                key = next((elem for elem in state["key-value"]
                            if elem["key"] == "YWNjb3VudEluZm8="), None)
                decoded_balances[state.get("id", "")] = unpack_data(
                    key["value"].get("bytes"), BALANCE_DECODE_FORMAT)
            except Exception:
                pass

        return decoded_balances

    def _check_maintenance_mode(self):
        if self.maintenance_mode_status != 0:
            raise Exception(
                "ULTRADE APPLICATION IS CURRENTLY IN MAINTENANCE MODE. PLACING AND CANCELING ORDERS IS TEMPORARY DISABLED")
