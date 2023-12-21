import json
import aiohttp
from algosdk.v2client.algod import AlgodClient

from .socket_client import SocketClient
from .algod_service import AlgodService
from .constants import NETWORK_CONSTANTS
from . import socket_options
from .types import ClientOptions, Network, CreateOrder
from .signers.main import Signer
from .encode import make_create_order_msg
from typing import Literal, Optional

OPTIONS = socket_options

class Client:
    """
    UltradeSdk client. Provides methods for creating and canceling orders on Ultrade exchange and subscribing to Ultrade data streams.
    """

    def __init__(self, network: Literal[Network.MAINNET, Network.TESTNET], **kwargs: Optional[ClientOptions]):
        if not Network.is_valid_value(network):
            raise ValueError("Network should be either mainnet or testnet")
        
        self.network = network
        self.options = kwargs or {}
        self.__configure()

    def __configure(self):
        network_constants = NETWORK_CONSTANTS.get(self.network)

        if not network_constants:
            raise ValueError(f"Unknown network: {self.network}")
        
        algod_base_url = network_constants["node"]
        indexer_base_url = network_constants["indexer"]
        ws_base_url = network_constants["websocket_url"]
        base_url = network_constants["api_url"]
        
        self.api_url = self.options.get('api_url', base_url)
        self.algod_node = self.options.get('algod_node', algod_base_url)
        self.algod_indexer = self.options.get('algod_indexer', indexer_base_url)
        self.websocket_url = self.options.get('websocket_url', ws_base_url)

        self.algod_client = self.options.get('algo_sdk_client', AlgodClient("", self.algod_node))
        if self.algod_client.genesis().get("network") != self.network:
            raise ValueError("Network of the AlgodClient should be the same as the network specified in the options")
        self.client = AlgodService(self.algod_client)

    def __validate_signer(self, signer: Signer):
        if not isinstance(signer, Signer):
            raise ValueError("parameter signer should be instance of Signer")

    def get_url_options(self) -> dict:
        """
        Returns the API and websocket URLs that client is using.
        """
        return {
            "api_url": self.api_url,
            "websocket_url": self.websocket_url,
            "algod_node": self.algod_node,
            "algod_indexer": self.algod_indexer
        }

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
                "address": signer.get_address(),
                "provider": signer.get_provider_name(),
            }
            message = json.dumps(data, separators=(',', ':'))
            message_bytes = message.encode('utf-8')
            signature = signer.sign_data(message_bytes)
            signature_hex = signature.hex() if isinstance(signature, bytes) else signature

            async with aiohttp.ClientSession() as session:
                url = f"{self.api_url}/wallet/signin"
                async with session.put(url, json={"data": data, "signature": signature_hex}) as resp:
                    response = await resp.text()
                    if "error" in response:
                        raise Exception(response["error"])
                    if response:
                        self.token = response
                        self.login_user = signer
            

    def is_logged_in(self):
        """
        Returns True if the client is logged in, otherwise returns False.
        """
        return self.login_user is not None and self.token is not None


    def __check_is_logged_in(self):
        if not self.is_logged_in():
            raise Exception("You need to login first")


    async def create_order(self, order: CreateOrder):
        """
        Creates an order using the provided order data.

        Args:
            order (CreateOrder): The order data.

        Returns:
            dict: The response from the server.

        Raises:
            Exception: If there is an error in the response.
        """
        self.__check_is_logged_in()
        self.__check_maintenance_mode()

        signer = self.login_user
        data = order.data
        encoding = 'hex'
        message_bytes = make_create_order_msg(data)
        message = message_bytes.decode(encoding)
        signature = signer.sign_data(message_bytes)
        signature_hex = signature.hex() if isinstance(signature, bytes) else signature
        url = f"{self.api_url}/market/order"
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json={"data": data, "encoding": encoding, "message": message, "signature": signature_hex}) as resp:
                response = await resp.json()
                if "error" in response:
                    raise Exception(response["error"])
                if response:
                    return response


    async def cancel_order(self, order_id):
        self.__check_is_logged_in()
        self.__check_maintenance_mode()

        signer = self.login_user
        data = {
            "orderId": order_id,
            "address": signer.get_address(),
        }
        message = json.dumps(data, separators=(',', ':'))
        message_bytes = message.encode('utf-8')
        signature = signer.sign_data(message_bytes)
        signature_hex = signature.hex() if isinstance(signature, bytes) else signature
        url = f"{self.api_url}/market/order"
        async with aiohttp.ClientSession() as session:
            async with session.delete(url, json={"data": { "data": data, "signature": signature_hex }}) as resp:
                response = await resp.json()
                if "error" in response:
                    raise Exception(response["error"])
                if response:
                    return response


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


    def __check_maintenance_mode(self):
        if self.maintenance_mode_status != 0:
            raise Exception(
                "ULTRADE APPLICATION IS CURRENTLY IN MAINTENANCE MODE. PLACING AND CANCELING ORDERS IS TEMPORARY DISABLED")
