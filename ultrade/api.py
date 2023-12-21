import time
from typing import Dict

import aiohttp

from .utils import construct_query_string_for_api_request
from .types import Network, ApiOptions
from typing import Optional

class Api:
    """
    Ultrade API client. Provides methods for getting data from Ultrade exchange.
    """

    def __init__(self, network: Network, **kwargs: Optional[ApiOptions]):
        options: ApiOptions = kwargs
        self.__set_network_urls(network, options)

    def __set_network_urls(self, network: Network, options: ApiOptions):
        base_url = f"https://api.{network}.ultrade.org"
        algod_base_url = f"https://{network}-api.algonode.cloud"
        indexer_base_url = f"https://{network}-idx.algonode.cloud"

        self.api_url = options.get('api_url', base_url)
        self.algod_node = options.get('algod_node', algod_base_url)
        self.algod_indexer = options.get('algod_indexer', indexer_base_url)


    async def get_pair_list(company_id=1):
        """
        Get pair list for the specified company_id
        If company_id is None, returns info about all existing pairs

        Args:
            company_id (int, default=1)

        Returns:
            dict
        """
        session = aiohttp.ClientSession()
        query = "" if company_id is None else f"?companyId={company_id}"
        url = f"{get_api_domain()}/market/markets{query}"
        async with session.get(url) as resp:
            data = await resp.json()
            await session.close()

            return data


    async def _get_exchange_info_old(identifier):
        data = await get_pair_list()

        try:
            identifier = int(identifier)
            key = "application_id"
        except ValueError:
            key = "pair_key"

        for dict in data:
            if dict[key] == identifier:
                return dict

        raise Exception("Can't find exchange info for the specified symbol")


    async def get_exchange_info(symbol):
        """
        Get info about specified pair

        Args:
            symbol (str): symbol represents existing pair, example: 'algo_usdt'

        Returns:
            dict
        """

        session = aiohttp.ClientSession()
        url = f"{get_api_domain()}/market/market?symbol={symbol}"
        async with session.get(url) as resp:
            resp.raise_for_status()
            data = await resp.json()

            await session.close()
        return data


    async def ping():
        """
        Check connection with server

        Returns:
            int: latency of the sent request in ms
        """
        session = aiohttp.ClientSession()
        url = f"{get_api_domain()}/system/time"
        async with session.get(url) as resp:
            resp.raise_for_status()
            data = await resp.json()

            await session.close()
            return round(time.time() * 1000) - data['currentTime']


    async def get_price(symbol):
        """
        Get prices for the specified pair

        Args:
            symbol (str): symbol represents existing pair, example: 'algo_usdt'

        Returns:
            dict
        """
        session = aiohttp.ClientSession()
        url = f"{get_api_domain()}/market/price?symbol={symbol}"
        async with session.get(url) as resp:
            data = await resp.json()
            await session.close()
            return data


    async def get_depth(symbol, depth=100):
        """
        Get depth for specified symbol from the Ultrade exchange

        Args:
            symbol (str): symbol represents existing pair, example: 'algo_usdt'
            depth (int, default=100, max_value=100)

        Returns:
            dict: order book for the specified pair
        """
        session = aiohttp.ClientSession()
        url = f"{get_api_domain()}/market/depth?symbol={symbol}&depth={depth}"
        async with session.get(url) as resp:
            data = await resp.json()
            await session.close()
            return data


    async def get_symbols(mask) -> Dict[str, str]:
        """
        Return example: For mask="algo_usdt" -> [{'pairKey': 'algo_usdt'}]

        Returns:
            list
        """
        session = aiohttp.ClientSession()
        url = f"{get_api_domain()}/market/symbols?mask={mask}"
        async with session.get(url) as resp:
            data = await resp.json()
            await session.close()
            return data


    async def get_history(symbol, interval=None, start_time=None, end_time=None, limit=None, page=None):
        """
        Returns:
            dict
        """
        query_string = construct_query_string_for_api_request(locals())
        session = aiohttp.ClientSession()
        url = f"{get_api_domain()}/market/history{query_string}"
        async with session.get(url) as resp:
            data = await resp.json()
            await session.close()
            return data


    async def get_last_trades(symbol):
        """
        Get last trades for the specified symbol

        Args:
            symbol (str): symbol represents existing pair, example: 'algo_usdt'

        Returns:
            list
        """
        session = aiohttp.ClientSession()
        url = f"{get_api_domain()}/market/last-trades?symbol={symbol}"
        async with session.get(url) as resp:
            data = await resp.json()
            await session.close()
            return data


    async def _get_encoded_balance(address, app_id):
        # todo: remove
        session = aiohttp.ClientSession()
        url = f"{get_algod_indexer_domain()}/v2/accounts/{address}?include-all=true"
        async with session.get(url) as resp:
            data = await resp.json()
            await session.close()
            state = next((state for state in data["account"].get(
                'apps-local-state') if state["id"] == app_id and state["deleted"] is False), None)
            if not state:
                return None

            key = next((elem for elem in state["key-value"]
                        if elem["key"] == "YWNjb3VudEluZm8="), None)
            if not key:
                raise Exception(
                    "Error: can't find balance value for the specified application_id")

            return key["value"].get("bytes")


    async def get_min_algo_balance(address):
        """
        Get min algo balance of the wallet

        Args:
            address (str)

        Returns:
            int: sum of minimum algo for the current wallet and additional algo buffer set by SDK.
        """
        session = aiohttp.ClientSession()
        url = f"{get_algod_node_domain()}/v2/accounts/{address}"
        async with session.get(url) as resp:
            algo_buffer = 1000000
            data = await resp.json()
            await session.close()
            min_balance = data.get("min-balance", {})
            return min_balance + algo_buffer

    async def get_orders_with_trades(address, symbol=None, status="OPEN_ORDER"):
        """
        Get orders with trades for the specified address

        Args:
            address (str)
            symbol (str, optional)
            status (str, default="OPEN_ORDER")

        Returns:
            list
        """
        session = aiohttp.ClientSession()
        url = f"{get_api_domain()}/market/orders-with-trades?address={address}&status={status}"
        if symbol:
            url += f"&symbol={symbol}"
        async with session.get(url) as resp:
            data = await resp.json()
            await session.close()
            return data
        
    async def get_orders(symbol=None, status=1, start_time=None, end_time=None, limit=500):
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
        url = f"{get_api_domain()}/market/orders?status={status}&limit={limit}"
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

    async def get_wallet_transactions(address, symbol=None):
        """
        Get wallet transactions for the specified address

        Args:
            address (str)
            symbol (str, optional)

        Returns:
            list
        """
        session = aiohttp.ClientSession()
        url = f"{get_api_domain()}/market/wallet-transactions?address={address}"
        if symbol:
            url += f"&symbol={symbol}"
        async with session.get(url) as resp:
            data = await resp.json()
            await session.close()
            return data

    async def get_order_by_id(order_id):
        """
        Get order by id

        Args:
            order_id (int)

        Returns:
            dict
        """
        session = aiohttp.ClientSession()
        url = f"{get_api_domain()}/market/getOrderById?orderId={order_id}"
        async with session.get(url) as resp:
            data = await resp.json()
            await session.close()
            return data

    async def get_balances():
        """
        Get balances of the wallet
        
        Returns:
            dict: balances of the wallet
        """
        session = aiohttp.ClientSession()
        url = f"{get_api_domain()}/market/balances"
        async with session.get(url) as resp:
            data = await resp.json()
            await session.close()
            return data
        
    async def get_company_by_domain(domain):
        """
        Get company by domain without https:// or / at the end
        
        Args:
            domain (str): Example: "app.ultrade.org"
        
        Returns:
            dict: company info
        """
        print("get_company_by_domain", domain)
        headers = {"wl-domain": domain}
        url = f"{get_api_domain()}/market/settings"
        print("url", url)
        session = aiohttp.ClientSession()
        async with session.get(url, headers=headers) as resp:
            data = await resp.json()
            await session.close()
            return data