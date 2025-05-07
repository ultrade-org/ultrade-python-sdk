import aiohttp
from algosdk.v2client.algod import AlgodClient
from .socket_client import SocketClient
from .utils.algod_service import AlgodService
from .utils.utils import get_wh_id_by_address, toJson
from .constants import NETWORK_CONSTANTS, DEFAULT_LOGIN_MESSAGE
from . import socket_options
from .types import (
    ClientOptions,
    Depth,
    LastTrade,
    Network,
    CreateOrder,
    Balance,
    OrderStatus,
    OrderWithTrade,
    Price,
    Symbol,
    WalletTransactions,
    TradingPair,
    PairInfo,
    AuthMethod,
)
from .signers.main import Signer
from .utils.encode import get_order_bytes, make_withdraw_msg
from typing import Literal, Optional, List, Dict
import time
from urllib.parse import urlparse, urlunparse

OPTIONS = socket_options


class CompanyNotEnabledException(Exception):
    pass


class Client:
    """
    UltradeSdk client. Provides methods for creating and canceling orders on Ultrade exchange and subscribing to Ultrade data streams.
    """

    def __init__(
        self,
        network: Literal[Network.MAINNET, Network.TESTNET],
        **kwargs: Optional[ClientOptions],
    ):
        if not Network.is_valid_value(network):
            raise ValueError("Network should be either mainnet or testnet")
        self.network = network
        self.__options = kwargs or {}
        self.__configure()
        self._login_user: Optional[Signer] = None
        self._token: Optional[str] = None
        self._trading_key_data: Optional[Dict[str, str]] = None
        self._trading_key_signer: Optional[Signer] = None
        self._company_id = self.__options.get("company_id", 1)

    def __configure(self):
        network_constants = NETWORK_CONSTANTS.get(self.network)

        if not network_constants:
            raise ValueError(f"Unknown network: {self.network}")

        algod_base_url = network_constants["node"]
        indexer_base_url = network_constants["indexer"]
        ws_base_url = network_constants["websocket_url"]
        base_url = network_constants["api_url"]

        api_url = self.__options.get("api_url", base_url).rstrip("/")
        parsed = urlparse(api_url)

        if parsed.username:
            self.__private_api_key = parsed.username
            clean_netloc = parsed.hostname
            if parsed.port:
                clean_netloc += f":{parsed.port}"
            clean_url = urlunparse(parsed._replace(netloc=clean_netloc))
            self.__api_url = clean_url
        else:
            self.__private_api_key = None
            self.__api_url = api_url

        self.__algod_node = self.__options.get("algod_node", algod_base_url).rstrip("/")
        self.__algod_indexer = self.__options.get(
            "algod_indexer", indexer_base_url
        ).rstrip("/")
        self.__websocket_url = self.__options.get("websocket_url", ws_base_url).rstrip(
            "/"
        )

        self.__algod_client = self.__options.get(
            "algo_sdk_client", AlgodClient("", self.__algod_node)
        )
        if self.__algod_client.genesis().get("network") != self.network:
            raise ValueError(
                "Network of the AlgodClient should be the same as the network specified in the options"
            )
        self._client = AlgodService(self.__algod_client)
        self._websocket_client = SocketClient(self.__websocket_url)

    def __validate_signer(self, signer: Signer):
        if not isinstance(signer, Signer):
            raise ValueError("parameter signer should be instance of Signer")

    async def __fetch_tmc_configuration(self):
        url = f"{self.__api_url}/market/chains"
        async with aiohttp.ClientSession(self.__no_auth_headers) as session:
            async with session.get(url) as resp:
                data = await resp.json()
                return data

    async def __get_codex_app_id(self):
        url = f"{self.__api_url}/market/codex-app-id"
        async with aiohttp.ClientSession(self.__no_auth_headers) as session:
            async with session.get(url) as resp:
                app_id = await resp.text()
                return int(app_id)

    @property
    def __auth_headers(self):
        headers = {}
        if self._login_user and self._token:
            headers["X-Wallet-Address"] = self._login_user.address
            headers["X-Wallet-Token"] = self._token

        if self._trading_key_data:
            headers["X-Trading-Key"] = self._trading_key_data["trading_key"]
            headers["X-Wallet-Address"] = self._trading_key_data["address"]
        if self.__private_api_key:
            headers["x-api-key"] = self.__private_api_key

        return headers

    @property
    def __no_auth_headers(self):
        headers = {}
        if self.__private_api_key:
            headers["x-api-key"] = self.__private_api_key

        return headers

    def __disconnect_login_user(self):
        self._login_user = None
        self._token = None

    def __disconnect_trading_key(self):
        self._trading_key_data = None
        self._trading_key_signer = None

    def _check_auth_method(self):
        if self._login_user and self._token:
            return AuthMethod.LOGIN
        if self._trading_key_data and self._trading_key_signer:
            return AuthMethod.TRADING_KEY
        return AuthMethod.NONE

    def set_trading_key(
        self, trading_key: str, address: str, trading_key_mnemonic: str
    ):
        """
        Sets the trading key for the SDK client. This method is used to authenticate the client with the Ultrade exchange.
        Alternatively, you can use the `set_login_user` method to authenticate the client.

        Args:
            trading_key (str): The trading key.
            address (str): The address of the trading key.
            trading_key_mnemonic (str): The mnemonic of the trading key. The mnemonic is a string of words that is generated when you register a trading key

        Raises:
            Exception: If there is an error in the response from the server.

        """
        self._trading_key_data = {
            "trading_key": trading_key,
            "address": address,
            "mnemonic": trading_key_mnemonic,
        }
        trading_key_signer = Signer.create_signer(trading_key_mnemonic)
        self._trading_key_signer = trading_key_signer
        self.__disconnect_login_user()

    async def set_login_user(self, signer: Signer):
        """
        Sets the login user for the SDK client. This method is used to authenticate the client with the Ultrade exchange.
        Alternatively, you can use the `set_trading_key` method to authenticate the client.

        Args:
            signer (Signer): The signer object representing the user.

        Raises:
            Exception: If there is an error in the response from the server.

        """
        self.__validate_signer(signer)

        data = {"address": signer.address, "technology": signer.provider_name}
        message = DEFAULT_LOGIN_MESSAGE
        message_bytes = message.encode("utf-8")
        message_hex = message_bytes.hex()
        signature = signer.sign_data(message_bytes)
        signature_hex = signature.hex() if isinstance(signature, bytes) else signature
        headers = {
            "CompanyId": str(self._company_id),
        }
        if self.__private_api_key:
            headers["x-api-key"] = self.__private_api_key
        async with aiohttp.ClientSession(headers=headers) as session:
            url = f"{self.__api_url}/wallet/signin"
            async with session.put(
                url,
                json={"data": data, "message": message_hex, "signature": signature_hex},
            ) as resp:
                response = await resp.text()
                if "error" in response:
                    raise Exception(response["error"])
                if response:
                    self._token = response
                    self._login_user = signer
                    self.__disconnect_trading_key()

    def is_logged_in(self):
        """
        Returns True if the client is logged in, otherwise returns False.
        """
        auth_method = self._check_auth_method()
        return auth_method != AuthMethod.NONE

    def __check_is_logged_in(self):
        if not self.is_logged_in():
            raise Exception("You need to login or specify trading key first")

    async def _build_order_payload(
        self,
        pair_id: int,
        order_side: str,
        order_type: str,
        amount: int,
        price: int,
        seconds_until_expiration: int
    ):
        self.__check_is_logged_in()

        if order_side not in ["B", "S"]:
            raise ValueError("order_side must be 'B' (buy) or 'S' (sell)")

        if order_type not in ["M", "L", "I", "P"]:
            raise ValueError("order_type must be 'M' (market), 'L' (limit), 'I' (ioc), or 'P' (post only)")

        auth_method = self._check_auth_method()
        if auth_method == AuthMethod.TRADING_KEY:
            login_address = self._trading_key_data["address"]
            login_chain_id = get_wh_id_by_address(login_address)
            signer = self._trading_key_signer
        else:
            login_address = self._login_user.address
            login_chain_id = self._login_user.wormhole_chain_id
            signer = self._login_user

        pair = await self.get_pair_info(pair_id)
        if not pair:
            raise Exception(f"Pair with id {pair_id} not found")

        decimal_price = price / 10 ** 18
        order_msg_version = 1
        expiration_date_in_seconds = int(time.time()) + seconds_until_expiration

        order = CreateOrder(
            order_msg_version,
            pair_id=pair_id,
            company_id=self._company_id,
            login_address=login_address,
            login_chain_id=login_chain_id,
            order_side=order_side,
            order_type=order_type,
            amount=amount,
            price=price,
            decimal_price=decimal_price,
            base_token_address=pair["base_id"],
            base_token_chain_id=pair["base_chain_id"],
            price_token_address=pair["price_id"],
            price_token_chain_id=pair["price_chain_id"],
            expiration_date_in_seconds=expiration_date_in_seconds
        )

        data = order.data
        encoding = "hex"
        message_bytes = get_order_bytes(data)
        message = message_bytes.hex()
        signature = signer.sign_data(message_bytes)
        signature_hex = signature.hex() if isinstance(signature, bytes) else signature

        return {
            "data": data,
            "encoding": encoding,
            "message": message,
            "signature": signature_hex,
        }

    async def create_order(
        self,
        pair_id: int,
        order_side: str,
        order_type: str,
        amount: int,
        price: int,
        seconds_until_expiration: int = 3660,
    ):
        """
        Creates an order using the provided order data.

        Args:
            pair_id (int): The ID of the trading pair.
            order_side (str): The side of the order. Must be 'B' (buy) or 'S' (sell).
            order_type (str): The type of the order. Must be 'M' (market), 'L' (limit), 'I' (ioc), or 'P' (post only).
            amount (int): The amount of the order.
            price (int): The price of the order.
            seconds_until_expiration (int): Seconds until the order expires, default=3600

        Returns:
            dict: The response from the server.

        Raises:
            ValueError: If the order_side or order_type is invalid.
            Exception: If there is an error in the response.
        """
        payload = await self._build_order_payload(
            pair_id, order_side, order_type, amount, price, seconds_until_expiration
        )
        url = f"{self.__api_url}/market/order"
        async with aiohttp.ClientSession(headers=self.__auth_headers) as session:
            async with session.post(url, json=payload) as resp:
                response = await resp.json()
                if "error" in response:
                    raise Exception(response)
                return response

    async def create_bulk_orders(self, orders: list[dict]) -> list[dict]:
        """
        Creates multiple orders in a single batch.

        Args:
            orders (list[dict]): List of order dicts with keys:
                pair_id, order_side, order_type, amount, price, seconds_until_expiration (optional)

        Returns:
            list[dict]: List of responses from the server.
        """
        url = f"{self.__api_url}/market/orders"
        signed_order_list = []
        for order in orders:
            signed_order = await self._build_order_payload(
                order["pair_id"],
                order["order_side"],
                order["order_type"],
                order["amount"],
                order["price"],
                order.get("seconds_until_expiration", 3660),
                )
            signed_order_list.append(signed_order)

        async with aiohttp.ClientSession(headers=self.__auth_headers) as session:
            async with session.post(url, json={ "arrayData": signed_order_list }) as resp:
                response = await resp.json()
                if "error" in response:
                    raise Exception(response)
            return response

    def _build_cancel_order_payload(self, data):
        auth_method = self._check_auth_method()

        if auth_method == AuthMethod.TRADING_KEY:
            # login_address = self._trading_key_data["address"]
            signer = self._trading_key_signer
        else:
            # login_address = self._login_user.address
            signer = self._login_user

        message = toJson(data)
        message_bytes = message.encode("utf-8")
        signature = signer.sign_data(message_bytes)
        signature_hex = signature.hex() if isinstance(signature, bytes) else signature

        return {"signature": signature_hex, "data": data}

    async def cancel_order(self, order_id) -> None:
        """
        Cancels the order with the specified ID.

        Args:
            order_id (int): The ID of the order to cancel.

        Returns: void if the order was successfully canceled.

        Raises:
            Exception: If there is an error in the response from the server.
            For example:
            Exception: {'statusCode': 404, 'message': 'Order not found', 'error': 'Not Found'}

        """
        self.__check_is_logged_in()
        body = self._build_cancel_order_payload({ "orderId": order_id })
        url = f"{self.__api_url}/market/order"

        async with aiohttp.ClientSession(headers=self.__auth_headers) as session:
            async with session.delete(url, json=body) as resp:
                response = await resp.json(content_type=None)
                if response is None:
                    return
                if "error" in response:
                    raise Exception(response)
                return response

    async def cancel_bulk_orders(self, order_ids: list[int], pair_id: str) -> list:
        """
        Cancels multiple orders by their IDs.

        Args:
            order_ids (list[int]): A list of order IDs to cancel.

        Returns:
            list: A list of results for each cancel attempt.
        """
        self.__check_is_logged_in()
        body = self._build_cancel_order_payload({ "orderIds": order_ids, "pairId": pair_id })
        url = f"{self.__api_url}/market/orders"

        async with aiohttp.ClientSession(headers=self.__auth_headers) as session:
            async with session.delete(url, json=body) as resp:
                response = await resp.json(content_type=None)
                if response is None:
                    return
                if "error" in response:
                    raise Exception(response)
                return response

    async def get_balances(self) -> List[Balance]:
        """
        Returns the balances of the logged user.

        Returns:
            list of dict: logged user balances.
            - hash (str) - hash of the balance
            - loginAddress (str) - address of the user
            - loginChainId (int) - chain id of the user
            - tokenId (int) - id of the token in the database
            - tokenChainId  (int) - chain id of the token
            - tokenAddress (str | int) - contract address of the token
            - amount (int) - amount of the token
            - lockedAmount (int) - locked amount of the token
        """
        self.__check_is_logged_in()
        url = f"{self.__api_url}/market/balances"
        async with aiohttp.ClientSession(headers=self.__auth_headers) as session:
            async with session.get(url) as resp:
                data = await resp.json()
                return data

    async def get_orders_with_trades(
        self, symbol=None, status=OrderStatus.OPEN_ORDER.value
    ) -> List[OrderWithTrade]:
        """
        Returns the orders of the logged user.

        Args:
            symbol (str): The symbol of the pair.
            status (OrderStatus): The status of the orders.

        Returns:
            List[OrderWithTrade]
        """
        self.__check_is_logged_in()
        if isinstance(status, OrderStatus):
            status_value = status.value
        else:
            status_value = status
        login_address = (
            self._login_user.address
            if self._login_user
            else self._trading_key_data["address"]
        )
        url = f"{self.__api_url}/market/orders-with-trades?address={login_address}&status={status_value}"
        if symbol:
            url += f"&symbol={symbol}"
        async with aiohttp.ClientSession(headers=self.__auth_headers) as session:
            async with session.get(url) as resp:
                data = await resp.json()
                return data

    async def get_wallet_transactions(
        self,
        startTime: Optional[int] = None,
        endTime: Optional[int] = None,
        page: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> List[WalletTransactions]:
        """
        Returns list of transactions (deposit/witdraw) of the logged user.

         Args:
            startTime (int, optional): The start time for filtering transactions.
            endTime (int, optional): The end time for filtering transactions.
            page (int, optional): The page number for pagination.
            limit (int, optional): The number of transactions per page.

        Returns:
            list
        """
        self.__check_is_logged_in()
        login_address = (
            self._login_user.address
            if self._login_user
            else self._trading_key_data["address"]
        )
        query_params = {
            "address": login_address,
            "startTime": startTime,
            "endTime": endTime,
            "page": page,
            "limit": limit,
        }
        query_params = {k: v for k, v in query_params.items() if v is not None}
        url = f"{self.__api_url}/wallet/transactions"
        async with aiohttp.ClientSession(headers=self.__auth_headers) as session:
            async with session.get(url, params=query_params) as resp:
                data = await resp.json()
                await session.close()

        for transaction in data:
            transaction.pop("vaa_message", None)

        return data

    async def withdraw(
        self,
        amount: int,
        token_address: str,
        token_chain_id: int,
        recipient: str,
        is_native_token: bool = False,
    ):
        """
        Withdraws the specified amount of tokens to the specified recipient.

        Args:
            amount (int): The amount of tokens to withdraw.
            token_address (str): The address of the token to withdraw.
            token_chain_id (int): The chain ID of the token to withdraw.
            recipient (str): The address of the recipient.
            is_native_token (bool, optional): Whether the token is native to the chain. Defaults to False.

        Returns:
            dict: The response from the server.
        """
        self.__check_is_logged_in()
        auth_method = self._check_auth_method()
        if auth_method == AuthMethod.TRADING_KEY:
            raise Exception("Trading key can't withdraw, use set_login_user method")
        signer = self._login_user

        recipient_chain_id = token_chain_id
        fee = int(amount * 0.01)  # 1% fee hadrcode, temporary solution

        data = {
            "loginAddress": signer.address,
            "loginChainId": signer.wormhole_chain_id,
            "tokenAmount": amount,
            "tokenIndex": token_address,
            "recipient": recipient,
            "recipientChainId": recipient_chain_id,
            "isNative": is_native_token,
            "fee": fee,
        }

        message_bytes = make_withdraw_msg(
            signer.address,
            signer.wormhole_chain_id,
            recipient,
            recipient_chain_id,
            amount,
            token_address,
            is_native_token,
            fee,
            data,
        )

        message = message_bytes.hex()
        signature = signer.sign_data(message_bytes)
        signature_hex = signature.hex() if isinstance(signature, bytes) else signature
        url = f"{self.__api_url}/wallet/withdraw"
        async with aiohttp.ClientSession(headers=self.__auth_headers) as session:
            async with session.post(
                url,
                json={
                    "encoding": "hex",
                    "message": message,
                    "signature": signature_hex,
                    "destinationAddress": recipient,
                },
            ) as resp:
                response = await resp.json()
                return response

    async def deposit(
        self, signer: Signer, amount: int, token_address: str | int, rpc_url=None
    ) -> str:
        """
        Deposit a specified amount of tokens into the Token Manager Contract.

        This method facilitates the depositing of a certain amount of tokens to the Token Manager Contract.
        To use this function, create a 'Signer' instance from the mnemonic of the wallet that will be used
        as the deposit source to the Token Manager Contract. It is essential that the 'Signer' wallet is
        part of the same blockchain network as the asset that is intended to be deposited.

        For deposits into EVM-compatible networks (such as Ethereum, Polygon, Binance Smart Chain, etc.),
        the 'rpc_url' parameter is required to specify the network's RPC URL. For other blockchain networks,
        this parameter is not necessary and can be left as default (None).

        Args:
            signer (Signer): The 'Signer' instance created from the wallet's mnemonic. This wallet will be
                             used as the source for the deposit and must belong to the same network as the
                             asset being deposited.
            amount (int): The amount of tokens to deposit.
            token_address (str | int): The ID of the token to be deposited.
            rpc_url (str, optional): The RPC URL of the EVM-compatible chain where the deposit will be made.
                                     This is required for EVM networks. Defaults to None.

        Returns:
            str: The transaction ID of the deposit transaction.

        Raises:
            ValueError: If any of the required parameters are invalid or missing.
        """
        self.__check_is_logged_in()
        auth_method = self._check_auth_method()
        if auth_method == AuthMethod.TRADING_KEY:
            raise Exception("Trading key can't deposit, use set_login_user method")
        self.__validate_signer(signer)

        tmc_configs = await self.__fetch_tmc_configuration()
        codex_app_id = await self.__get_codex_app_id()

        config = {}
        config["rpc_url"] = rpc_url
        config["algod_client"] = self.__algod_client
        config["tmc_configs"] = tmc_configs
        config["login_user"] = self._login_user
        config["codex_app_id"] = codex_app_id

        return await signer._deposit(amount, token_address, config)

    async def subscribe(self, subscribe_options, callback):
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
        self.__check_is_logged_in()

        def socket_callback(event, args):
            return callback(event, args)

        if subscribe_options.get("address") is None:
            subscribe_options["address"] = (
                self._login_user.address
                if self._login_user
                else self._trading_key_data["address"]
            )

        auth_method = self._check_auth_method()

        if auth_method == AuthMethod.LOGIN:
            subscribe_options["options"]["token"] = self._token
        elif auth_method == AuthMethod.TRADING_KEY:
            signer = self._trading_key_signer
            message = "Grant access by trading key"

            message_bytes = message.encode("utf-8")
            message_hex = message_bytes.hex()
            signature = signer.sign_data(message_bytes)

            subscribe_options["options"]["message"] = message_hex
            subscribe_options["options"]["signature"] = signature
            subscribe_options["options"]["tradingKey"] = self._trading_key_data["trading_key"]
        if OPTIONS.MAINTENANCE not in subscribe_options["streams"]:
            subscribe_options["streams"].append(OPTIONS.MAINTENANCE)
        if OPTIONS.ERROR not in subscribe_options["streams"]:
            subscribe_options["streams"].append(OPTIONS.ERROR)

        return await self._websocket_client.subscribe(subscribe_options, socket_callback)

    async def unsubscribe(self, connection_id):
        """
        Unsubscribe from a websocket connection.

        Args:
            connection_id (str): The ID of the connection to unsubscribe from.
        """
        await self._websocket_client.unsubscribe(connection_id)

    # def __check_maintenance_mode(self):
    #     if self.maintenance_mode_status != 0:
    #         raise Exception(
    #             "ULTRADE APPLICATION IS CURRENTLY IN MAINTENANCE MODE. PLACING AND CANCELING ORDERS IS TEMPORARY DISABLED"
    #         )
    async def get_pair_list(self) -> List[TradingPair]:
        """
        Retrieves a list of trading pairs available on the exchange for a specific company.

        Args:
            company_id (int, optional): The unique identifier of the company. Defaults to None, in which case all trading pairs will be returned.

        Returns:
            List[TradingPair]: A list containing trading pair information. Each trading pair is represented as a dictionary with specific attributes like 'pairName', 'baseCurrency', etc.

        Raises:
            aiohttp.ClientError: If an error occurs during the HTTP request.
        """
        session = aiohttp.ClientSession(headers=self.__auth_headers)
        query = "" if self._company_id is None else f"?companyId={self._company_id}"
        url = f"{self.__api_url}/market/markets{query}"
        async with session.get(url) as resp:
            data = await resp.json()
            await session.close()

            return data

    async def get_pair_info(self, symbol: str) -> PairInfo:
        """
        Retrieves detailed information about a specific trading pair.

        Args:
            symbol (str): The symbol representing the trading pair, e.g., 'algo_usdt'.

        Returns:
            dict: PairInfo.
        """

        session = aiohttp.ClientSession(self.__no_auth_headers)
        url = f"{self.__api_url}/market/market?symbol={symbol}"
        async with session.get(url) as resp:
            resp.raise_for_status()
            data = await resp.json()

            await session.close()
        return data

    async def ping(self):
        """
        Checks the latency between the client and the server by measuring the time taken for a round-trip request.

        Returns:
            int: The round-trip latency in milliseconds.
        """
        session = aiohttp.ClientSession(self.__no_auth_headers)
        url = f"{self.__api_url}/system/time"
        async with session.get(url) as resp:
            resp.raise_for_status()
            data = await resp.json()

            await session.close()
            return round(time.time() * 1000) - data["currentTime"]

    async def get_price(self, symbol: str) -> Price:
        """
        Retrieves the current market price for a specified trading pair.

        Args:
            symbol (str): The symbol representing the trading pair, e.g., 'algo_usdt'.

        Returns:
            dict: A dictionary containing price information like the current ask, bid, and last trade price.
        """
        session = aiohttp.ClientSession(self.__no_auth_headers)
        url = f"{self.__api_url}/market/price?symbol={symbol}"
        async with session.get(url) as resp:
            data = await resp.json()
            await session.close()
            return data

    async def get_depth(self, symbol: str, depth: int = 100) -> Depth:
        """
        Retrieves the order book depth for a specified trading pair, showing the demand and supply at different price levels.

        Args:
            symbol (str): The symbol representing the trading pair, e.g., 'algo_usdt'.
            depth (int, optional): The depth of the order book to retrieve. Defaults to 100.

        Returns:
            dict: A dictionary representing the order book with lists of bids and asks.
        """
        session = aiohttp.ClientSession(self.__no_auth_headers)
        url = f"{self.__api_url}/market/depth?symbol={symbol}&depth={depth}"
        async with session.get(url) as resp:
            data = await resp.json()
            await session.close()
            return data

    async def get_symbols(self, mask) -> List[Symbol]:
        """
        Return example: For mask="algo" -> [{'pairKey': 'algo_usdt'}]

        Args:
            mask (str): A pattern or partial symbol to filter the trading pairs, e.g., 'algo'.

        Returns:
            list: A list of dictionaries, each containing a 'pairKey' that matches the provided mask.
        """
        session = aiohttp.ClientSession(self.__no_auth_headers)
        url = f"{self.__api_url}/market/symbols?mask={mask}"
        async with session.get(url) as resp:
            data = await resp.json()
            await session.close()
            return data

    async def get_last_trades(self, symbol: str) -> List[LastTrade]:
        """
        Retrieves the most recent trades for a specified trading pair.

        Args:
            symbol (str): The symbol representing the trading pair, e.g., 'algo_usdt'.

        Returns:
            LastTrade
            list: A list of the most recent trades for the specified trading pair.
        """
        session = aiohttp.ClientSession(self.__no_auth_headers)
        url = f"{self.__api_url}/market/last-trades?symbol={symbol}"
        async with session.get(url) as resp:
            data = await resp.json()
            await session.close()
            return data

    async def get_order_by_id(self, order_id: int) -> OrderWithTrade:
        """
        Retrieves detailed information about an order based on its unique identifier.

        Args:
            order_id (int): The unique identifier of the order.

        Returns:
            dict: A dictionary containing detailed information about the specified order.
        """
        self.__check_is_logged_in()
        session = aiohttp.ClientSession(headers=self.__auth_headers)
        url = f"{self.__api_url}/market/order/{order_id}"
        async with session.get(url) as resp:
            data = await resp.json()
            await session.close()
            return data

    @staticmethod
    async def get_company_by_domain(self, domain: str) -> int:
        """
        Retrieves the company ID based on the domain name.

        Args:
            domain (str): The domain of the company'.
                        Example: "app.ultrade.org" or "https://app.ultrade.org/"

        Returns:
            int: The company ID.

        Raises:
            CompanyNotEnabledException: If the company is not enabled or
                                        if an error occurs during the API request.
        """
        domain = domain.replace("https://", "").replace("http://", "").rstrip("/")

        headers = {"wl-domain": domain}
        if self.__private_api_key:
            headers["x-api-key"] = self.__private_api_key

        url = f"{self.__api_url}/market/settings"
        session = aiohttp.ClientSession()
        async with session.get(url, headers=headers) as resp:
            data = await resp.json()
            await session.close()
            is_enabled = bool(int(data["company.enabled"]))
            if not is_enabled:
                raise CompanyNotEnabledException(
                    f"Company with {domain} domain is not enabled"
                )
            return data["companyId"]

    async def get_avaible_chains(self) -> List[str]:
        """
        Retrieves the list of available chains.

        Returns:
            list: A list of available chains.
        """
        config = await self.__fetch_tmc_configuration()
        return [chain["name"] for chain in config]

    async def get_cctp_assets(self) -> dict:
        """
        Retrieves the CCTP assets from the market endpoint.

        Returns:
            dict: A dictionary containing the CCTP assets.
        """
        url = f"{self.__api_url}/market/cctp-assets"
        async with aiohttp.ClientSession(headers=self.__auth_headers) as session:
            async with session.get(url) as resp:
                data = await resp.json()
                return data

    async def get_cctp_unified_assets(self) -> dict:
        """
        Retrieves the unified CCTP assets from the market endpoint.

        Returns:
            dict: A dictionary containing the unified CCTP assets.
        """
        url = f"{self.__api_url}/market/cctp-unified-assets"
        async with aiohttp.ClientSession(headers=self.__auth_headers) as session:
            async with session.get(url) as resp:
                data = await resp.json()
                return data

    async def get_assets(self) -> List[Dict]:
        """
        Returns the list of market assets:
        - id (int): The ID of the asset.
        - address (str): The address of the asset.
        - chainId (int): The chain ID of the asset.
        - name (str): The name of the asset.
        - unitName (str): The unit name of the asset.
        - decimals (int): The number of decimals of the asset.
        - isGas (bool): Whether the asset is gas.
        """
        url = f"{self.__api_url}/market/assets"
        async with aiohttp.ClientSession(headers=self.__auth_headers) as session:
            async with session.get(url) as resp:
                data = await resp.json()
                return data

    async def get_orders(
        self,
        startTime: Optional[int] = None,
        endTime: Optional[int] = None,
        page: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> List[WalletTransactions]:
        # todo update, add 'status' query param
        """
        Returns list of logged user orders.

         Args:
            startTime (int, optional): The start time for filtering transactions.
            endTime (int, optional): The end time for filtering transactions.
            page (int, optional): The page number for pagination.
            limit (int, optional): The number of transactions per page.

        Returns:
            list of dict - logged user orders.
        """
        self.__check_is_logged_in()

        query_params = {
            "startTime": startTime,
            "endTime": endTime,
            "page": page,
            "limit": limit,
        }
        query_params = {k: v for k, v in query_params.items() if v is not None}
        url = f"{self.__api_url}/market/orders"
        async with aiohttp.ClientSession(headers=self.__auth_headers) as session:
            async with session.get(url, params=query_params) as resp:
                data = await resp.json()
                await session.close()
                return data
