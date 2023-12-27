import time
from typing import Dict, List
from .types import TradingPair

import aiohttp
from .utils import construct_query_string_for_api_request


class CompanyNotEnabledException(Exception):
    pass


class Api:
    def __init__(self, api_url: str, algod_node: str, algod_indexer: str):
        """
        Initializes the API object.

        Args:
            api_url (str): The URL of the API.
            algod_node (str): The URL of the Algod node.
            algod_indexer (str): The URL of the Algod indexer.
        """
        self.api_url = api_url
        self.algod_node = algod_node
        self.algod_indexer = algod_indexer

    async def get_pair_list(self, company_id=1) -> List[TradingPair]:
        """
        Retrieves a list of trading pairs from the API.

        Args:
            company_id (int, optional): The ID of the company. Defaults to 1.

        Returns:
            List[TradingPair]: A list of trading pair data, where each trading pair is a dictionary
                            with specific attributes (as defined in TradingPair TypedDict).

        Raises:
            aiohttp.ClientError: If there is an error with the HTTP request.
        """
        session = aiohttp.ClientSession()
        query = "" if company_id is None else f"?companyId={company_id}"
        url = f"{self.api_url}/market/markets{query}"
        async with session.get(url) as resp:
            data = await resp.json()
            await session.close()

            return data

    async def _get_exchange_info_old(self, identifier):
        data = await self.get_pair_list()

        try:
            identifier = int(identifier)
            key = "application_id"
        except ValueError:
            key = "pair_key"

        for dict in data:
            if dict[key] == identifier:
                return dict

        raise Exception("Can't find exchange info for the specified symbol")

    async def get_exchange_info(self, symbol):
        """
        Get info about specified pair

        Args:
            symbol (str): symbol represents existing pair, example: 'algo_usdt'

        Returns:
            dict
        """

        session = aiohttp.ClientSession()
        url = f"{self.api_url}/market/market?symbol={symbol}"
        async with session.get(url) as resp:
            resp.raise_for_status()
            data = await resp.json()

            await session.close()
        return data

    async def ping(self):
        """
        Check connection with server

        Returns:
            int: latency of the sent request in ms
        """
        session = aiohttp.ClientSession()
        url = f"{self.api_url}/system/time"
        async with session.get(url) as resp:
            resp.raise_for_status()
            data = await resp.json()

            await session.close()
            return round(time.time() * 1000) - data["currentTime"]

    async def get_price(self, symbol):
        """
        Get prices for the specified pair

        Args:
            symbol (str): symbol represents existing pair, example: 'algo_usdt'

        Returns:
            dict
        """
        session = aiohttp.ClientSession()
        url = f"{self.api_url}/market/price?symbol={symbol}"
        async with session.get(url) as resp:
            data = await resp.json()
            await session.close()
            return data

    async def get_depth(self, symbol, depth=100):
        """
        Get depth for specified symbol from the Ultrade exchange

        Args:
            symbol (str): symbol represents existing pair, example: 'algo_usdt'
            depth (int, default=100, max_value=100)

        Returns:
            dict: order book for the specified pair
        """
        session = aiohttp.ClientSession()
        url = f"{self.api_url}/market/depth?symbol={symbol}&depth={depth}"
        async with session.get(url) as resp:
            data = await resp.json()
            await session.close()
            return data

    async def get_symbols(self, mask) -> Dict[str, str]:
        """
        Return example: For mask="algo_usdt" -> [{'pairKey': 'algo_usdt'}]

        Returns:
            list
        """
        session = aiohttp.ClientSession()
        url = f"{self.api_url}/market/symbols?mask={mask}"
        async with session.get(url) as resp:
            data = await resp.json()
            await session.close()
            return data

    async def get_history(
        self,
        symbol,
        interval=None,
        start_time=None,
        end_time=None,
        limit=None,
        page=None,
    ):
        """
        Returns:
            dict
        """
        query_string = construct_query_string_for_api_request(locals())
        session = aiohttp.ClientSession()
        url = f"{self.api_url}/market/history{query_string}"
        async with session.get(url) as resp:
            data = await resp.json()
            await session.close()
            return data

    async def get_last_trades(self, symbol):
        """
        Get last trades for the specified symbol

        Args:
            symbol (str): symbol represents existing pair, example: 'algo_usdt'

        Returns:
            list
        """
        session = aiohttp.ClientSession()
        url = f"{self.api_url}/market/last-trades?symbol={symbol}"
        async with session.get(url) as resp:
            data = await resp.json()
            await session.close()
            return data

    async def get_min_algo_balance(self, address):
        """
        Get min algo balance of the wallet

        Args:
            address (str)

        Returns:
            int: sum of minimum algo for the current wallet and additional algo buffer set by SDK.
        """
        session = aiohttp.ClientSession()
        url = f"{self.algod_node}/v2/accounts/{address}"
        async with session.get(url) as resp:
            algo_buffer = 1000000
            data = await resp.json()
            await session.close()
            min_balance = data.get("min-balance", {})
            return min_balance + algo_buffer

    async def get_orders(
        self, symbol=None, status=1, start_time=None, end_time=None, limit=500
    ):
        """
        Get orders for the specified symbol

        Args:
            symbol (str, optional)
            status (int, default=1)
            start_time (int, optional)
            end_time (int, optional)
            limit (int, default=500)

        Returns:
            list
        """
        session = aiohttp.ClientSession()
        url = f"{self.api_url}/market/orders?status={status}&limit={limit}"
        if symbol:
            url += f"&symbol={symbol}"
        if start_time:
            url += f"&startTime={start_time}"
        if end_time:
            url += f"&endTime={end_time}"
        async with session.get(url) as resp:
            data = await resp.json()
            await session.close()
            return data

    async def get_order_by_id(self, order_id):
        """
        Get order by id

        Args:
            order_id (int)

        Returns:
            dict
        """
        session = aiohttp.ClientSession()
        url = f"{self.api_url}/market/getOrderById?orderId={order_id}"
        async with session.get(url) as resp:
            data = await resp.json()
            await session.close()
            return data

    async def get_company_by_domain(self, domain: str) -> int:
        """
        Get company settings by domain.

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
        url = f"{self.api_url}/market/settings"
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
