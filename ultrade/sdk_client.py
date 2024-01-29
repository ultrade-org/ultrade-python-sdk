import json
import aiohttp
from algosdk.v2client.algod import AlgodClient

from .socket_client import SocketClient
from .algod_service import AlgodService
from .constants import NETWORK_CONSTANTS
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
    WalletOperations,
    TradingPair,
    PairInfo,
)
from .signers.main import Signer
from .encode import get_order_bytes, make_withdraw_msg
from typing import Literal, Optional, List, Dict
import time

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

    def __configure(self):
        network_constants = NETWORK_CONSTANTS.get(self.network)

        if not network_constants:
            raise ValueError(f"Unknown network: {self.network}")

        algod_base_url = network_constants["node"]
        indexer_base_url = network_constants["indexer"]
        ws_base_url = network_constants["websocket_url"]
        base_url = network_constants["api_url"]

        self.__api_url = self.__options.get("api_url", base_url).rstrip("/")
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
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                data = await resp.json()
                return data

    async def __get_codex_app_id(self):
        url = f"{self.__api_url}/market/codex-app-id"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                app_id = await resp.text()
                return int(app_id)

    @property
    def __headers(self):
        headers = {}
        if self._login_user and self._token:
            headers["X-Wallet-Address"] = self._login_user.address
            headers["X-Wallet-Token"] = self._token
        return headers

    async def set_login_user(self, signer: Signer):
        """
        Sets the login user for the SDK client.

        Args:
            signer (Signer): The signer object representing the user.

        Raises:
            Exception: If there is an error in the response from the server.

        """
        self.__validate_signer(signer)

        data = {
            "address": signer.address,
            "provider": signer.provider_name,
        }
        message = json.dumps(data, separators=(",", ":"))
        message_bytes = message.encode("utf-8")
        signature = signer.sign_data(message_bytes)
        signature_hex = signature.hex() if isinstance(signature, bytes) else signature

        async with aiohttp.ClientSession() as session:
            url = f"{self.__api_url}/wallet/signin"
            async with session.put(
                url, json={"data": data, "signature": signature_hex}
            ) as resp:
                response = await resp.text()
                if "error" in response:
                    raise Exception(response["error"])
                if response:
                    self._token = response
                    self._login_user = signer

    def is_logged_in(self):
        """
        Returns True if the client is logged in, otherwise returns False.
        """
        return self._login_user is not None and self._token is not None

    def __check_is_logged_in(self):
        if not self.is_logged_in():
            raise Exception("You need to login first")

    async def create_order(
        self,
        pair_id: int,
        order_side: str,
        order_type: str,
        amount: int,
        price: int,
        wlp_id: int = 0,
        company_id: int = 1,
    ):
        """
        Creates an order using the provided order data.

        Args:
            pair_id (int): The ID of the trading pair.
            order_side (str): The side of the order. Must be 'B' (buy) or 'S' (sell).
            order_type (str): The type of the order. Must be 'M' (market), 'L' (limit), 'I' (ioc), or 'P' (post only).
            amount (int): The amount of the order.
            price (int): The price of the order.
            wlp_id (int, optional): The ID of the WLP. Defaults to 0.
            company_id (int, optional): The ID of the company. Defaults to 1.

        Returns:
            dict: The response from the server.

        Raises:
            ValueError: If the order_side or order_type is invalid.
            Exception: If there is an error in the response.
        """
        self.__check_is_logged_in()
        if order_side not in ["B", "S"]:
            raise ValueError("order_side must be 'B' (buy) or 'S' (sell)")

        if order_type not in ["M", "L", "I", "P"]:
            raise ValueError(
                "order_type must be 'M' (market), 'L' (limit), 'I' (ioc), or 'P' (post only)"
            )
        # self.__check_maintenance_mode()
        signer = self._login_user
        pair = await self.get_pair_info(pair_id)
        if not pair:
            raise Exception(f"Pair with id {pair_id} not found")

        order = CreateOrder(
            pair_id=pair_id,
            company_id=company_id,
            login_address=signer.address,
            login_chain_id=signer.wormhole_chain_id,
            order_side=order_side,
            order_type=order_type,
            amount=amount,
            price=price,
            base_token_address=pair["base_id"],
            base_token_chain_id=pair["base_chain_id"],
            price_token_address=pair["price_id"],
            price_token_chain_id=pair["price_chain_id"],
            wlp_id=wlp_id,
        )
        data = order.data
        encoding = "hex"
        message_bytes = get_order_bytes(data)
        message = message_bytes.hex()
        signature = signer.sign_data(message_bytes)
        signature_hex = signature.hex() if isinstance(signature, bytes) else signature
        url = f"{self.__api_url}/market/order"
        async with aiohttp.ClientSession(headers=self.__headers) as session:
            async with session.post(
                url,
                json={
                    "data": data,
                    "encoding": encoding,
                    "message": message,
                    "signature": signature_hex,
                },
            ) as resp:
                response = await resp.json(content_type=None)
                if response is None:
                    return
                if "error" in response:
                    raise Exception(response)

    async def cancel_order(self, order_id):
        self.__check_is_logged_in()
        # self.__check_maintenance_mode()

        signer = self._login_user
        data = {
            "orderId": order_id,
            "address": signer.address,
        }
        message = json.dumps(data, separators=(",", ":"))
        message_bytes = message.encode("utf-8")
        signature = signer.sign_data(message_bytes)
        signature_hex = signature.hex() if isinstance(signature, bytes) else signature
        body = {"signature": signature_hex, "data": data}
        url = f"{self.__api_url}/market/order"
        async with aiohttp.ClientSession(headers=self.__headers) as session:
            async with session.delete(url, json=body) as resp:
                response = await resp.json(content_type=None)
                if response is None:
                    return
                if "error" in response:
                    raise Exception(response)
                else:
                    return response

    async def get_balances(self) -> List[Balance]:
        """
        Returns the balances of the logged user.

        Returns:
            list of dict: logged user balances.
            - hash (str)
            - loginAddress (str)
            - loginChainId (int)
            - tokenId (int or str)
            - tokenChainId  (int)
            - amount (int)
            - lockedAmount (int)
        """
        self.__check_is_logged_in()
        url = f"{self.__api_url}/market/balances"
        async with aiohttp.ClientSession(headers=self.__headers) as session:
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
        url = f"{self.__api_url}/market/orders-with-trades?address={self._login_user.address}&status={status_value}"
        if symbol:
            url += f"&symbol={symbol}"
        async with aiohttp.ClientSession(headers=self.__headers) as session:
            async with session.get(url) as resp:
                data = await resp.json()
                return data

    async def get_operations(self) -> List[WalletOperations]:
        """
        Returns list of operation (deposit/witdraw) of the logged user.

        Args:
            symbol (str, optional): The symbol of the pair.

        Returns:
            list
        """
        self.__check_is_logged_in()
        url = f"{self.__api_url}/market/wallet-transactions?address={self._login_user.address}"
        async with aiohttp.ClientSession(headers=self.__headers) as session:
            async with session.get(url) as resp:
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
    ):
        """
        Withdraws the specified amount of tokens to the specified recipient.

        Args:
            amount (int): The amount of tokens to withdraw.
            token_address (str): The address of the token to withdraw.
            token_chain_id (int): The chain ID of the token to withdraw.
            recipient (str): The address of the recipient.

        Returns:
            dict: The response from the server.
        """
        self.__check_is_logged_in()
        signer = self._login_user

        recipient_chain_id = token_chain_id
        message_bytes = make_withdraw_msg(
            signer.address,
            signer.wormhole_chain_id,
            recipient,
            recipient_chain_id,
            amount,
            token_address,
            token_chain_id,
        )
        data = {
            "loginAddress": signer.address,
            "loginChainId": signer.wormhole_chain_id,
            "tokenAmount": amount,
            "tokenIndex": token_address,
            "tokenChainId": token_chain_id,
            "recipient": recipient,
            "recipientChainId": recipient_chain_id,
        }
        message = message_bytes.hex()
        signature = signer.sign_data(message_bytes)
        signature_hex = signature.hex() if isinstance(signature, bytes) else signature
        url = f"{self.__api_url}/wallet/withdraw"
        async with aiohttp.ClientSession(headers=self.__headers) as session:
            async with session.post(
                url,
                json={
                    "data": data,
                    "encoding": "hex",
                    "message": message,
                    "signature": signature_hex,
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
            options["address"] = self._login_user.address

        if OPTIONS.MAINTENANCE not in options["streams"]:
            options["streams"].append(OPTIONS.MAINTENANCE)

        return await self._websocket_client.subscribe(options, socket_callback)

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
    async def get_pair_list(self, company_id=None) -> List[TradingPair]:
        """
        Retrieves a list of trading pairs available on the exchange for a specific company.

        Args:
            company_id (int, optional): The unique identifier of the company. Defaults to None, in which case all trading pairs will be returned.

        Returns:
            List[TradingPair]: A list containing trading pair information. Each trading pair is represented as a dictionary with specific attributes like 'pairName', 'baseCurrency', etc.

        Raises:
            aiohttp.ClientError: If an error occurs during the HTTP request.
        """
        session = aiohttp.ClientSession()
        query = "" if company_id is None else f"?companyId={company_id}"
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

        session = aiohttp.ClientSession()
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
        session = aiohttp.ClientSession()
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
        session = aiohttp.ClientSession()
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
        session = aiohttp.ClientSession()
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
        session = aiohttp.ClientSession()
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
        session = aiohttp.ClientSession()
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
        session = aiohttp.ClientSession()
        url = f"{self.__api_url}/market/getOrderById?orderId={order_id}"
        async with session.get(url) as resp:
            data = await resp.json()
            await session.close()
            return data["order"][0]

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
