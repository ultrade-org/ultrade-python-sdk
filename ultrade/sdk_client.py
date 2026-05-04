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
from .utils.encode import (
    make_spot_order_msg,
    make_perp_order_msg,
    make_withdraw_msg,
    make_transfer_msg,
    SPOT_TRANSFER_DOMAIN,
    MM_DEPOSIT_DOMAIN,
    MM_WITHDRAW_DOMAIN,
    MM_BORROW_DOMAIN,
    MM_REPAY_DOMAIN,
)
from typing import Any, Literal, Optional, List, Dict, Tuple
import asyncio
import time
from urllib.parse import urlparse, urlunparse
import random

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

        # Shared HTTP session (lazy: created on first use so the constructor is
        # safe to call outside an event loop).
        self._session: Optional[aiohttp.ClientSession] = None
        self._connector_limit: int = self.__options.get("http_connection_limit", 64)

        # Pair info TTL cache and one-shot caches for static config.
        self._pair_info_cache: Dict[Any, Tuple[float, dict]] = {}
        self._pair_info_ttl: float = float(self.__options.get("pair_info_ttl", 60.0))
        self._tmc_configuration: Optional[list] = None
        self._codex_app_id: Optional[int] = None

    def _http(self) -> aiohttp.ClientSession:
        """Lazy-init shared aiohttp session. Reuses TLS / TCP connections.
        Recreated automatically if the running event loop changes (e.g. when
        running under pytest-asyncio with per-test loops)."""
        try:
            current_loop = asyncio.get_running_loop()
        except RuntimeError:
            current_loop = None
        existing_loop = getattr(self._session, "_loop", None) if self._session else None
        if (
            self._session is None
            or self._session.closed
            or (current_loop is not None and existing_loop is not current_loop)
        ):
            self._session = aiohttp.ClientSession(
                connector=aiohttp.TCPConnector(limit=self._connector_limit),
            )
        return self._session

    async def close(self) -> None:
        """Close the shared HTTP session. Safe to call multiple times."""
        if self._session is not None and not self._session.closed:
            await self._session.close()
        self._session = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.close()

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
        if self._tmc_configuration is not None:
            return self._tmc_configuration
        url = f"{self.__api_url}/market/chains"
        async with self._http().get(url, headers=self.__no_auth_headers) as resp:
            self._tmc_configuration = await resp.json()
            return self._tmc_configuration

    async def __get_codex_app_id(self):
        if self._codex_app_id is not None:
            return self._codex_app_id
        url = f"{self.__api_url}/market/codex-app-id"
        async with self._http().get(url, headers=self.__no_auth_headers) as resp:
            self._codex_app_id = int(await resp.text())
            return self._codex_app_id

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
            headers["X-API-Key"] = self.__private_api_key

        return headers

    @property
    def __no_auth_headers(self):
        headers = {}
        if self.__private_api_key:
            headers["X-API-Key"] = self.__private_api_key

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
        signature_hex = ("0x" + signature.hex()) if isinstance(signature, bytes) else signature
        headers = {
            "CompanyId": str(self._company_id),
        }
        if self.__private_api_key:
            headers["X-API-Key"] = self.__private_api_key
        url = f"{self.__api_url}/wallet/signin"
        async with self._http().put(
            url,
            headers=headers,
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
        seconds_until_expiration: int,
        max_total: Optional[int] = None,
        order_flags: int = 0,
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

        order_msg_version = 1
        expiration_date_in_seconds = int(time.time()) + seconds_until_expiration

        # `amount` is size8 (humanAmount * 10^8) and `price` is price10
        # (humanPrice * 10^10) for spot. maxTotal is humanTotal in size8 too,
        # so maxTotal = humanAmount * humanPrice * 10^8 = amount*price / 10^10.
        if max_total is None:
            max_total = (int(amount) * int(price)) // (10 ** 10)

        data = {
            "version": order_msg_version,
            "expiredTime": expiration_date_in_seconds,
            "orderSide": order_side,
            "price": price,
            "amount": amount,
            "orderType": order_type,
            "address": login_address,
            "chainId": login_chain_id,
            "baseTokenAddress": pair["base_id"],
            "baseTokenChainId": pair["base_chain_id"],
            "priceTokenAddress": pair["price_id"],
            "priceTokenChainId": pair["price_chain_id"],
            "companyId": self._company_id,
            "maxTotal": max_total,
            "orderFlags": order_flags,
        }

        message_bytes = make_spot_order_msg(data)
        message = message_bytes.hex()
        signature = signer.sign_data(message_bytes)
        signature_hex = ("0x" + signature.hex()) if isinstance(signature, bytes) else signature

        return {
            "message": message,
            "signature": signature_hex,
        }

    async def _build_perp_order_payload(
        self,
        pair_id: int,
        pyth_id: str,
        order_side: int,
        order_type: int,
        time_in_force: int,
        flags: int,
        size_lots: int,
        limit_price: int,
        target_leverage: int,
        trigger_price: int = 0,
        seconds_until_expiration: int = 3660,
        twap_end_time: int = 0,
    ):
        self.__check_is_logged_in()

        auth_method = self._check_auth_method()
        if auth_method == AuthMethod.TRADING_KEY:
            login_address = self._trading_key_data["address"]
            login_chain_id = get_wh_id_by_address(login_address)
            signer = self._trading_key_signer
        else:
            login_address = self._login_user.address
            login_chain_id = self._login_user.wormhole_chain_id
            signer = self._login_user

        random_number = random.randint(1, 2**53 - 1)
        expiration_date_in_seconds = int(time.time()) + seconds_until_expiration

        data = {
            "address": login_address,
            "chainId": login_chain_id,
            "pythId": pyth_id,
            "orderSide": order_side,
            "orderType": order_type,
            "timeInForce": time_in_force,
            "flags": flags,
            "sizeLots": size_lots,
            "limitPrice": limit_price,
            "triggerPrice": trigger_price,
            "expiredTime": expiration_date_in_seconds,
            "twapEndTime": twap_end_time,
            "random": random_number,
            "targetLev": target_leverage,
            "companyId": self._company_id,
        }

        # Build the 130-byte perp order message locally — verified byte-identical
        # to /market/order/perp/message. Avoids one HTTP roundtrip per order.
        message_bytes = make_perp_order_msg(data)
        message_hex = message_bytes.hex()
        signature = signer.sign_data(message_bytes)
        signature_hex = ("0x" + signature.hex()) if isinstance(signature, bytes) else signature

        return {"message": message_hex, "signature": signature_hex}

    async def create_order(
        self,
        pair_id: int = None,
        order_side=None,
        order_type=None,
        amount: int = None,
        price: int = None,
        seconds_until_expiration: int = 3660,
        market_type: Literal["spot", "perp"] = "spot",
        *,
        pyth_id: str = None,
        time_in_force: int = None,
        flags: int = 0,
        size_lots: int = None,
        limit_price: int = None,
        trigger_price: int = 0,
        twap_end_time: int = 0,
        target_leverage: int = None,
    ):
        """
        Creates an order using the provided order data.

        Args:
            market_type (str): "spot" or "perp". Defaults to "spot".
            pair_id (int): The ID of the trading pair (both market types).
            seconds_until_expiration (int): Seconds until the order expires, default=3660.

        Spot-only:
            order_side (str): 'B' (buy) or 'S' (sell).
            order_type (str): 'M' (market), 'L' (limit), 'I' (ioc), or 'P' (post only).
            amount (int): The amount of the order.
            price (int): The price of the order in factored units.

        Perp-only (keyword args):
            pyth_id (str): Pyth feed id for the perp pair.
            order_side (int): Numeric perp order side.
            order_type (int): Numeric perp order type.
            time_in_force (int): Numeric time-in-force.
            flags (int): Order flags bitmask.
            size_lots (int): Order size in lots.
            limit_price (int): Limit price (atomic).
            trigger_price (int): Trigger price for stop orders (atomic).
            twap_end_time (int): TWAP end timestamp in seconds.
            target_leverage (int): Target leverage for isolated positions.

        Returns:
            dict: The response from the server.
        """
        if market_type == "perp":
            payload = await self._build_perp_order_payload(
                pair_id=pair_id,
                pyth_id=pyth_id,
                order_side=order_side,
                order_type=order_type,
                time_in_force=time_in_force,
                flags=flags,
                size_lots=size_lots,
                limit_price=limit_price,
                target_leverage=target_leverage,
                trigger_price=trigger_price,
                seconds_until_expiration=seconds_until_expiration,
                twap_end_time=twap_end_time,
            )
            payload["type"] = "perp"
        elif market_type == "spot":
            payload = await self._build_order_payload(
                pair_id, order_side, order_type, amount, price, seconds_until_expiration
            )
            payload["type"] = "spot"
        else:
            raise ValueError("market_type must be 'spot' or 'perp'")

        url = f"{self.__api_url}/market/order"
        async with self._http().post(url, json=payload, headers=self.__auth_headers) as resp:
                response = await resp.json(content_type=None)
                if resp.status >= 400 or (isinstance(response, dict) and "error" in response):
                    raise Exception(response)
                return response

    async def create_bulk_orders(
        self,
        orders: list[dict],
        market_type: Literal["spot", "perp"] = "spot",
    ) -> list[dict]:
        """
        Creates multiple orders in a single batch. All orders in the batch must
        be the same market_type.

        Args:
            orders (list[dict]): List of order dicts. Keys depend on market_type:
                spot: pair_id, order_side, order_type, amount, price, seconds_until_expiration (optional)
                perp: pair_id, pyth_id, order_side, order_type, time_in_force, flags,
                      size_lots, limit_price, target_leverage, trigger_price (opt),
                      twap_end_time (opt), seconds_until_expiration (opt)
            market_type (str): "spot" or "perp". Defaults to "spot".

        Returns:
            list[dict]: List of responses from the server.
        """
        if market_type == "perp":
            # Each perp order requires a roundtrip to /market/order/perp/message;
            # fan them out concurrently rather than serially awaiting each.
            signed_order_list = list(await asyncio.gather(*[
                self._build_perp_order_payload(
                    pair_id=order["pair_id"],
                    pyth_id=order["pyth_id"],
                    order_side=order["order_side"],
                    order_type=order["order_type"],
                    time_in_force=order["time_in_force"],
                    flags=order.get("flags", 0),
                    size_lots=order["size_lots"],
                    limit_price=order["limit_price"],
                    target_leverage=order["target_leverage"],
                    trigger_price=order.get("trigger_price", 0),
                    seconds_until_expiration=order.get("seconds_until_expiration", 3660),
                    twap_end_time=order.get("twap_end_time", 0),
                )
                for order in orders
            ]))
            for signed in signed_order_list:
                signed["type"] = "perp"
        elif market_type == "spot":
            signed_order_list = []
            for order in orders:
                signed = await self._build_order_payload(
                    order["pair_id"],
                    order["order_side"],
                    order["order_type"],
                    order["amount"],
                    order["price"],
                    order.get("seconds_until_expiration", 3660),
                )
                signed["type"] = "spot"
                signed_order_list.append(signed)
        else:
            raise ValueError("market_type must be 'spot' or 'perp'")

        url = f"{self.__api_url}/market/orders"
        async with self._http().post(url, json={"arrayData": signed_order_list}, headers=self.__auth_headers) as resp:
                response = await resp.json(content_type=None)
                if resp.status >= 400 or (isinstance(response, dict) and "error" in response):
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
        signature_hex = ("0x" + signature.hex()) if isinstance(signature, bytes) else signature

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

        async with self._http().delete(url, json=body, headers=self.__auth_headers) as resp:
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

        async with self._http().delete(url, json=body, headers=self.__auth_headers) as resp:
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
        url = f"{self.__api_url}/wallet/balances"
        async with self._http().get(url, headers=self.__auth_headers) as resp:
                data = await resp.json()
                return data

    async def get_orders_with_trades(
        self, symbol=None, status=OrderStatus.OPEN_ORDER.value
    ) -> List[OrderWithTrade]:
        """
        Returns the orders of the logged user. Address is taken from the
        authenticated session (X-Wallet-Address header).

        Args:
            symbol (str): The symbol of the pair.
            status (OrderStatus | int | list): The status(es) of the orders.

        Returns:
            List[OrderWithTrade]
        """
        self.__check_is_logged_in()

        def _normalize(s):
            if isinstance(s, OrderStatus):
                return str(s.value)
            return str(s)

        if isinstance(status, (list, tuple)):
            status_value = ",".join(_normalize(s) for s in status)
        else:
            status_value = _normalize(status)

        params = {"status": status_value}
        if symbol:
            params["symbol"] = symbol
        url = f"{self.__api_url}/market/orders"
        async with self._http().get(url, params=params, headers=self.__auth_headers) as resp:
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
        async with self._http().get(url, params=query_params, headers=self.__auth_headers) as resp:
            data = await resp.json()

        # The endpoint now returns {items: [...], ...}; fall back to a bare list.
        items = data["items"] if isinstance(data, dict) and "items" in data else data
        if isinstance(items, list):
            for transaction in items:
                if isinstance(transaction, dict):
                    transaction.pop("vaa_message", None)

        return items

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
        random_number = random.randint(1, 2**53 - 1)

        data = {
            "loginAddress": signer.address,
            "loginChainId": signer.wormhole_chain_id,
            "tokenAmount": amount,
            "tokenIndex": token_address,
            "recipient": recipient,
            "recipientChainId": recipient_chain_id,
            "isNative": is_native_token,
            "fee": fee,
            "random": random_number
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
            random_number,
            data,
        )

        message = message_bytes.hex()
        signature = signer.sign_data(message_bytes)
        signature_hex = ("0x" + signature.hex()) if isinstance(signature, bytes) else signature
        url = f"{self.__api_url}/wallet/withdraw"
        async with self._http().post(url,
                json={
                    "encoding": "hex",
                    "message": message,
                    "signature": signature_hex,
                    "destinationAddress": recipient,
                }, headers=self.__auth_headers) as resp:
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
        query = "" if self._company_id is None else f"?companyId={self._company_id}"
        url = f"{self.__api_url}/market/markets{query}"
        async with self._http().get(url, headers=self.__auth_headers) as resp:
            return await resp.json()

    async def get_pair_info(self, symbol: str) -> PairInfo:
        """
        Retrieves detailed information about a specific trading pair. Cached
        with a TTL (default 60s) to avoid redundant requests during bulk-order
        construction.

        Args:
            symbol (str): The symbol representing the trading pair, e.g., 'algo_usdt'.

        Returns:
            dict: PairInfo.
        """
        cached = self._pair_info_cache.get(symbol)
        if cached and (time.monotonic() - cached[0]) < self._pair_info_ttl:
            return cached[1]
        url = f"{self.__api_url}/market/market?symbol={symbol}"
        async with self._http().get(url, headers=self.__no_auth_headers) as resp:
            resp.raise_for_status()
            data = await resp.json()
        self._pair_info_cache[symbol] = (time.monotonic(), data)
        return data

    def invalidate_pair_info_cache(self, symbol: Optional[str] = None) -> None:
        """Drop one (or all) entries from the pair-info cache."""
        if symbol is None:
            self._pair_info_cache.clear()
        else:
            self._pair_info_cache.pop(symbol, None)

    async def ping(self):
        """
        Checks the latency between the client and the server by measuring the time taken for a round-trip request.

        Returns:
            int: The round-trip latency in milliseconds.
        """
        url = f"{self.__api_url}/system/time"
        async with self._http().get(url, headers=self.__no_auth_headers) as resp:
            resp.raise_for_status()
            data = await resp.json()
            return round(time.time() * 1000) - data["currentTime"]

    async def get_price(self, symbol: str) -> Price:
        """
        Retrieves the current market price for a specified trading pair.

        Args:
            symbol (str): The symbol representing the trading pair, e.g., 'algo_usdt'.

        Returns:
            dict: A dictionary containing price information like the current ask, bid, and last trade price.
        """
        url = f"{self.__api_url}/market/price?symbol={symbol}"
        async with self._http().get(url, headers=self.__no_auth_headers) as resp:
            return await resp.json()

    async def get_depth(self, symbol: str, depth: int = 100) -> Depth:
        """
        Retrieves the order book depth for a specified trading pair, showing the demand and supply at different price levels.

        Args:
            symbol (str): The symbol representing the trading pair, e.g., 'algo_usdt'.
            depth (int, optional): The depth of the order book to retrieve. Defaults to 100.

        Returns:
            dict: A dictionary representing the order book with lists of bids and asks.
        """
        url = f"{self.__api_url}/market/depth?symbol={symbol}&depth={depth}"
        async with self._http().get(url, headers=self.__no_auth_headers) as resp:
            return await resp.json()

    async def get_symbols(self, mask) -> List[Symbol]:
        """
        Return example: For mask="algo" -> [{'pairKey': 'algo_usdt'}]

        Args:
            mask (str): A pattern or partial symbol to filter the trading pairs, e.g., 'algo'.

        Returns:
            list: A list of dictionaries, each containing a 'pairKey' that matches the provided mask.
        """
        url = f"{self.__api_url}/market/symbols?mask={mask}"
        async with self._http().get(url, headers=self.__no_auth_headers) as resp:
            return await resp.json()

    async def get_last_trades(self, symbol: str) -> List[LastTrade]:
        """
        Retrieves the most recent trades for a specified trading pair.

        Args:
            symbol (str): The symbol representing the trading pair, e.g., 'algo_usdt'.

        Returns:
            LastTrade
            list: A list of the most recent trades for the specified trading pair.
        """
        url = f"{self.__api_url}/market/last-trades?symbol={symbol}"
        async with self._http().get(url, headers=self.__no_auth_headers) as resp:
            return await resp.json()

    async def get_order_by_id(self, order_id: int) -> OrderWithTrade:
        """
        Retrieves detailed information about an order based on its unique identifier.

        Args:
            order_id (int): The unique identifier of the order.

        Returns:
            dict: A dictionary containing detailed information about the specified order.
        """
        self.__check_is_logged_in()
        url = f"{self.__api_url}/market/order/{order_id}"
        async with self._http().get(url, headers=self.__auth_headers) as resp:
            return await resp.json()

    async def get_company_by_domain(self, domain: str) -> int:
        """
        Retrieves the company ID based on the domain name.

        Args:
            domain (str): The domain of the company.
                        Example: "app.ultrade.org" or "https://app.ultrade.org/"

        Returns:
            int: The company ID.

        Raises:
            CompanyNotEnabledException: If the company is not enabled or
                                        if an error occurs during the API request.
        """
        domain = domain.replace("https://", "").replace("http://", "").rstrip("/")

        headers = dict(self.__no_auth_headers)
        headers["wl-domain"] = domain

        url = f"{self.__api_url}/market/settings"
        async with self._http().get(url, headers=headers) as resp:
            data = await resp.json()
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
        async with self._http().get(url, headers=self.__auth_headers) as resp:
                data = await resp.json()
                return data

    async def get_cctp_unified_assets(self) -> dict:
        """
        Retrieves the unified CCTP assets from the market endpoint.

        Returns:
            dict: A dictionary containing the unified CCTP assets.
        """
        url = f"{self.__api_url}/market/cctp-unified-assets"
        async with self._http().get(url, headers=self.__auth_headers) as resp:
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
        async with self._http().get(url, headers=self.__auth_headers) as resp:
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
        async with self._http().get(url, params=query_params, headers=self.__auth_headers) as resp:
            return await resp.json()

    # ---------- Perps ----------

    async def get_positions(self) -> List[Dict]:
        """Returns the open perp positions of the logged user."""
        self.__check_is_logged_in()
        url = f"{self.__api_url}/wallet/positions"
        async with self._http().get(url, headers=self.__auth_headers) as resp:
                return await resp.json()

    async def get_equity(self) -> Dict:
        """Returns spot/perp balance and margin equity for the logged user."""
        self.__check_is_logged_in()
        url = f"{self.__api_url}/wallet/equity"
        async with self._http().get(url, headers=self.__auth_headers) as resp:
                return await resp.json()

    async def get_margin_assets(self) -> List[Dict]:
        """Returns the user's margin asset balances."""
        self.__check_is_logged_in()
        url = f"{self.__api_url}/wallet/margin-assets"
        async with self._http().get(url, headers=self.__auth_headers) as resp:
                return await resp.json()

    async def get_margin_assets_usd_value(self) -> Dict:
        """Returns the USD value of the user's margin assets portfolio."""
        url = f"{self.__api_url}/wallet/margin-assets/usd-value"
        async with self._http().get(url, headers=self.__auth_headers) as resp:
                return await resp.json()

    async def mark_margin_assets_to_now(self) -> Dict:
        """Marks the user's margin positions to the current price."""
        self.__check_is_logged_in()
        url = f"{self.__api_url}/wallet/margin-assets/mark-to-now"
        async with self._http().get(url, headers=self.__auth_headers) as resp:
                return await resp.json()

    async def get_market_margin_assets(self) -> List[Dict]:
        """Returns the list of margin assets supported by the market."""
        url = f"{self.__api_url}/market/margin-assets"
        async with self._http().get(url, headers=self.__auth_headers) as resp:
                return await resp.json()

    async def _build_transfer_payload(
        self,
        domain: str,
        token_amount: int,
        token_index: str,
        token_chain_id: int,
        recipient: Optional[str] = None,
        recipient_chain_id: Optional[int] = None,
        seconds_until_expiration: int = 60,
    ) -> Dict:
        """Builds a signed transfer payload locally with the given domain prefix.
        The domain selects which on-chain action the message is valid for
        (e.g. MM_DEPOSIT_V1 vs MM_WITHDRAW_V1)."""
        self.__check_is_logged_in()
        auth_method = self._check_auth_method()
        if auth_method == AuthMethod.TRADING_KEY:
            raise Exception("Trading key can't transfer, use set_login_user method")
        signer = self._login_user

        login_address = signer.address
        login_chain_id = signer.wormhole_chain_id
        rcpt = recipient if recipient is not None else login_address
        rcpt_chain = recipient_chain_id if recipient_chain_id is not None else login_chain_id
        expired_date = int(time.time()) + seconds_until_expiration

        message_bytes = make_transfer_msg(
            domain=domain,
            login_address=login_address,
            login_chain_id=login_chain_id,
            recipient=rcpt,
            recipient_chain_id=rcpt_chain,
            token_amount=token_amount,
            token_index=token_index,
            token_chain_id=token_chain_id,
            expired_date=expired_date,
        )
        message_hex = message_bytes.hex()
        signature = signer.sign_data(message_bytes)
        signature_hex = ("0x" + signature.hex()) if isinstance(signature, bytes) else signature
        return {"message": message_hex, "signature": signature_hex}

    async def _post_margin_asset_action(self, action: str, payload: Dict) -> Dict:
        url = f"{self.__api_url}/wallet/margin-asset/{action}"
        async with self._http().post(url, json=payload, headers=self.__auth_headers) as resp:
                response = await resp.json(content_type=None)
                if resp.status >= 400 or (isinstance(response, dict) and "error" in response):
                    raise Exception(response)
                return response

    async def deposit_margin_asset(
        self,
        token_amount: int,
        token_index: str,
        token_chain_id: int,
        seconds_until_expiration: int = 60,
    ) -> Dict:
        """Deposit margin collateral for perps trading."""
        payload = await self._build_transfer_payload(
            MM_DEPOSIT_DOMAIN, token_amount, token_index, token_chain_id,
            seconds_until_expiration=seconds_until_expiration,
        )
        return await self._post_margin_asset_action("deposit", payload)

    async def withdraw_margin_asset(
        self,
        token_amount: int,
        token_index: str,
        token_chain_id: int,
        seconds_until_expiration: int = 60,
    ) -> Dict:
        """Withdraw margin collateral from perps trading."""
        payload = await self._build_transfer_payload(
            MM_WITHDRAW_DOMAIN, token_amount, token_index, token_chain_id,
            seconds_until_expiration=seconds_until_expiration,
        )
        return await self._post_margin_asset_action("withdraw", payload)

    async def borrow_margin_asset(
        self,
        token_amount: int,
        token_index: str,
        token_chain_id: int,
        seconds_until_expiration: int = 60,
    ) -> Dict:
        """Borrow a margin asset against existing collateral."""
        payload = await self._build_transfer_payload(
            MM_BORROW_DOMAIN, token_amount, token_index, token_chain_id,
            seconds_until_expiration=seconds_until_expiration,
        )
        return await self._post_margin_asset_action("borrow", payload)

    async def repay_margin_asset(
        self,
        token_amount: int,
        token_index: str,
        token_chain_id: int,
        seconds_until_expiration: int = 60,
    ) -> Dict:
        """Repay a borrowed margin asset."""
        payload = await self._build_transfer_payload(
            MM_REPAY_DOMAIN, token_amount, token_index, token_chain_id,
            seconds_until_expiration=seconds_until_expiration,
        )
        return await self._post_margin_asset_action("repay", payload)

    async def replace_orders(
        self,
        replacements: list[dict],
        market_type: Literal["spot", "perp"] = "spot",
    ) -> List[Dict]:
        """
        Replace (amend) one or more existing orders. Each replacement cancels
        the old order and submits a new one atomically.

        Args:
            replacements (list[dict]): List of replacement dicts. Each must contain:
                old_order_id (int): The id of the order to replace.
                Plus order parameters matching the market_type, exactly as accepted by
                create_order (spot: pair_id/order_side/order_type/amount/price/...,
                perp: pair_id/pyth_id/order_side/order_type/time_in_force/...).
            market_type (str): "spot" or "perp". Defaults to "spot".

        Returns:
            list of dict: Results from the server.
        """
        if market_type not in ("spot", "perp"):
            raise ValueError("market_type must be 'spot' or 'perp'")

        url = f"{self.__api_url}/market/orders/replace"
        array_data = []
        for r in replacements:
            old_order_id = r["old_order_id"]
            if market_type == "perp":
                signed = await self._build_perp_order_payload(
                    pair_id=r["pair_id"],
                    pyth_id=r["pyth_id"],
                    order_side=r["order_side"],
                    order_type=r["order_type"],
                    time_in_force=r["time_in_force"],
                    flags=r.get("flags", 0),
                    size_lots=r["size_lots"],
                    limit_price=r["limit_price"],
                    target_leverage=r["target_leverage"],
                    trigger_price=r.get("trigger_price", 0),
                    seconds_until_expiration=r.get("seconds_until_expiration", 3660),
                    twap_end_time=r.get("twap_end_time", 0),
                )
            else:
                signed = await self._build_order_payload(
                    r["pair_id"],
                    r["order_side"],
                    r["order_type"],
                    r["amount"],
                    r["price"],
                    r.get("seconds_until_expiration", 3660),
                )
                signed = {"message": signed["message"], "signature": signed["signature"]}
            signed["oldOrderId"] = old_order_id
            signed["type"] = "perp" if market_type == "perp" else "spot"
            array_data.append(signed)

        async with self._http().post(url, json={"arrayData": array_data}, headers=self.__auth_headers) as resp:
                response = await resp.json(content_type=None)
                if resp.status >= 400 or (isinstance(response, dict) and "error" in response):
                    raise Exception(response)
                return response
