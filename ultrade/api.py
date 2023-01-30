import time
from typing import Dict

import aiohttp

from .constants import get_api_domain, get_algod_indexer_domain
from .utils import construct_query_string_for_api_request


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
        symbol
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
    Get prices for the specified pair from the server

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
        symbol (str): symbol represent existing pair, for example: 'algo_usdt'
        depth (int): depth for specific pair, max_value=100

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
    Return example: For mask="algo_u" -> [{'pairKey': 'algo_usdt'}]

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
    session = aiohttp.ClientSession()
    url = f"{get_algod_indexer_domain()}/v2/accounts/{address}?include-all=true"
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
