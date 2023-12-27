import time
from typing import Dict, List
from .types import TradingPair
import aiohttp


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
        Retrieves a list of trading pairs available on the exchange for a specific company.

        Args:
            company_id (int, optional): The unique identifier of the company. Defaults to 1, which usually represents the primary or default company.

        Returns:
            List[TradingPair]: A list containing trading pair information. Each trading pair is represented as a dictionary with specific attributes like 'pairName', 'baseCurrency', etc.

        Raises:
            aiohttp.ClientError: If an error occurs during the HTTP request.
        """
        session = aiohttp.ClientSession()
        query = "" if company_id is None else f"?companyId={company_id}"
        url = f"{self.api_url}/market/markets{query}"
        async with session.get(url) as resp:
            data = await resp.json()
            await session.close()

            return data

    async def get_exchange_info(self, symbol):
        """
        Retrieves detailed information about a specific trading pair.

        Args:
            symbol (str): The symbol representing the trading pair, e.g., 'algo_usdt'.

        Returns:
            dict: A dictionary containing detailed information about the trading pair, such as current price, trading volume, etc.
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
        Checks the latency between the client and the server by measuring the time taken for a round-trip request.

        Returns:
            int: The round-trip latency in milliseconds.
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
        Retrieves the current market price for a specified trading pair.

        Args:
            symbol (str): The symbol representing the trading pair, e.g., 'algo_usdt'.

        Returns:
            dict: A dictionary containing price information like the current ask, bid, and last trade price.
        """
        session = aiohttp.ClientSession()
        url = f"{self.api_url}/market/price?symbol={symbol}"
        async with session.get(url) as resp:
            data = await resp.json()
            await session.close()
            return data

    async def get_depth(self, symbol, depth=100):
        """
        Retrieves the order book depth for a specified trading pair, showing the demand and supply at different price levels.

        Args:
            symbol (str): The symbol representing the trading pair, e.g., 'algo_usdt'.
            depth (int, optional): The depth of the order book to retrieve. Defaults to 100.

        Returns:
            dict: A dictionary representing the order book with lists of bids and asks.
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

        Args:
            mask (str): A pattern or partial symbol to filter the trading pairs, e.g., 'algo'.

        Returns:
            list: A list of dictionaries, each containing a 'pairKey' that matches the provided mask.
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
        interval,
        start_time=None,
        end_time=None,
        limit=500,
        page=1,
    ):
        """
        Retrieves the trading history for a given symbol and interval.

        Args:
            symbol (str): Trading pair symbol, e.g., 'btc_usd'.
            interval (str): Interval for the trading data, e.g., '1m', '1h'.
            start_time (int, optional): Start timestamp for the history data.
            end_time (int, optional): End timestamp for the history data.
            limit (int, optional): The number of records to retrieve. Defaults to 500.
            page (int, optional): Page number for pagination. Defaults to 1.

        Returns:
            dict: A dictionary containing the trading history.
        """
        params = {
            "symbol": symbol,
            "interval": interval,
            "startTime": start_time if start_time is not None else "",
            "endTime": end_time if end_time is not None else "",
            "limit": limit,
            "page": page,
        }
        session = aiohttp.ClientSession()
        url = f"{self.api_url}/market/history"
        async with session.get(url, params=params) as resp:
            data = await resp.json()
            await session.close()
            return data

    async def get_last_trades(self, symbol):
        """
        Retrieves the most recent trades for a specified trading pair.

        Args:
            symbol (str): The symbol representing the trading pair, e.g., 'algo_usdt'.

        Returns:
            list: A list of the most recent trades for the specified trading pair.
        """
        session = aiohttp.ClientSession()
        url = f"{self.api_url}/market/last-trades?symbol={symbol}"
        async with session.get(url) as resp:
            data = await resp.json()
            await session.close()
            return data

    async def get_min_algo_balance(self, address):
        """
        Retrieves the minimum Algorand balance required for a wallet.

        Args:
            address (str): The Algorand wallet address.

        Returns:
            int: The minimum balance required in microAlgos
        """
        session = aiohttp.ClientSession()
        url = f"{self.algod_node}/v2/accounts/{address}"
        async with session.get(url) as resp:
            algo_buffer = 1000000
            data = await resp.json()
            await session.close()
            min_balance = data.get("min-balance", {})
            return min_balance + algo_buffer

    # TODO::Check this metod on the backend
    # async def get_orders(
    #     self, symbol=None, address="", status=1, start_time=None, end_time=None, limit=500
    # ):
    #     """
    #     Retrieves a list of orders based on various criteria such as symbol, status, and time range.

    #     Args:
    #         symbol (str, optional): The symbol representing the trading pair to filter orders.
    #         status (int, optional): The status of the orders to retrieve (e.g., open, closed). Defaults to 1 (open).
    #         start_time (int, optional): The start timestamp for filtering orders.
    #         end_time (int, optional): The end timestamp for filtering orders.
    #         limit (int, optional): The maximum number of orders to retrieve. Defaults to 500.

    #     Returns:
    #         list: A list of orders that match the specified criteria.
    #     """
    #     session = aiohttp.ClientSession()
    #     url = f"{self.api_url}/market/orders?status={status}&limit={limit}"
    #     if symbol:
    #         url += f"&symbol={symbol}"
    #     if start_time:
    #         url += f"&startTime={start_time}"
    #     if end_time:
    #         url += f"&endTime={end_time}"
    #     if address:
    #         url += f"&address={address}"
    #     async with session.get(url) as resp:
    #         data = await resp.json()
    #         await session.close()
    #         return data

    async def get_order_by_id(self, order_id):
        """
        Retrieves detailed information about an order based on its unique identifier.

        Args:
            order_id (int): The unique identifier of the order.

        Returns:
            dict: A dictionary containing detailed information about the specified order.
        """
        session = aiohttp.ClientSession()
        url = f"{self.api_url}/market/getOrderById?orderId={order_id}"
        async with session.get(url) as resp:
            data = await resp.json()
            await session.close()
            return data

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
