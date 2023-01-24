import time
from .constants import get_domain
from typing import Dict

import aiohttp


async def get_pair_list(partner_id=None):
    """
    Get pair list for the specified partner_id
    If partner_id is not specified, returns info about all existing pairs

    Args:
        partner_id (int, optional)

    Returns:
        dict
    """
    session = aiohttp.ClientSession()
    query = f"?partner_id={partner_id}" if partner_id else ""
    url = f"{get_domain()}/market/markets{query}"
    async with session.get(url) as resp:
        data = await resp.json()
        await session.close()

        return data


async def get_exchange_info(identifier):
    """
    Get info about specified pair

    Args:
        identifier (str|int): symbol or pair id
    Returns:
        dict
    """

    # should be replaced when dedicated endpoint is ready
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


async def ping():
    """
    Check connection with server

    Returns:
        int: latency of the sent request in ms
    """
    session = aiohttp.ClientSession()
    url = f"{get_domain()}/system/time"
    async with session.get(url) as resp:
        resp.raise_for_status()
        data = await resp.json()

        await session.close()
        return round(time.time() * 1000) - data['currentTime']


async def get_price(symbol):
    """
    Get prices for the specified pair from the server

    Returns:
        dict
    """
    session = aiohttp.ClientSession()
    url = f"{get_domain()}/market/price?symbol={symbol}"
    async with session.get(url) as resp:
        data = await resp.json()
        await session.close()
        return data


async def get_depth(symbol, depth=100):
    """
    Get depth for specified symbol from the Ultrade exchange

    Args:
        symbol (str): symbol represent existing pair, for example: 'algo_usdt'
        depth (int): depth for specific pair, max_value=100

    Returns:
        dict: order book for the specified pair
    """
    session = aiohttp.ClientSession()
    url = f"{get_domain()}/market/depth?symbol={symbol}&depth={depth}"
    async with session.get(url) as resp:
        data = await resp.json()
        await session.close()
        return data


async def get_symbols(mask) -> Dict[str, str]:
    """
    Return example: For mask="algo_u" -> [{'pairKey': 'algo_usdt'}]

    Returns:
        list
    """
    session = aiohttp.ClientSession()
    url = f"{get_domain()}/market/symbols?mask={mask}"
    async with session.get(url) as resp:
        data = await resp.json()
        await session.close()
        return data


async def get_history(symbol, interval="", start_time="", end_time="", limit=""):
    """
    Get trade history with graph data from the Ultrade exchange

    Returns:
        dict
    """
    session = aiohttp.ClientSession()
    url = f"{get_domain()}/market/history?symbol={symbol}&interval={interval}&startTime={start_time}&endTime={end_time}&limit={limit}"
    async with session.get(url) as resp:
        data = await resp.json()
        await session.close()
        return data


async def get_last_trades(symbol):
    # should work with user address
    """
    Get last trades for the specified symbol

    Args:
        symbol (str): symbol represents existing pair, example: 'algo_usdt'

    Returns:
        list
    """
    session = aiohttp.ClientSession()
    url = f"{get_domain()}/market/last-trades?symbol={symbol}"
    async with session.get(url) as resp:
        data = await resp.json()
        await session.close()
        return data


async def _get_encoded_balance(address, app_id):
    session = aiohttp.ClientSession()
    url = f"https://indexer.testnet.algoexplorerapi.io/v2/accounts/{address}?include-all=true"
    async with session.get(url) as resp:
        data = await resp.json()
        await session.close()
        state = next((state for state in data["account"].get(
            'apps-local-state') if state["id"] == app_id and state["deleted"] == False), None)
        if not state:
            return None

        key = next((elem for elem in state["key-value"]
                    if elem["key"] == "YWNjb3VudEluZm8="), None)
        if not key:
            raise Exception(
                "Error: can't find balance value for the specified application_id")

        return key["value"].get("bytes")
