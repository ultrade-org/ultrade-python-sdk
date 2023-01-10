import time
import requests
from .constants import get_domain

import aiohttp


async def get_exchange_info(identifier=None):
    # should be replaced when dedicated endpoint is ready
    session = aiohttp.ClientSession()
    url = f"{get_domain()}/market/markets"
    async with session.get(url) as resp:
        data = await resp.json()
        await session.close()

        if identifier == None:
            return data

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
    session = aiohttp.ClientSession()
    url = f"{get_domain()}/system/time"
    async with session.get(url) as resp:
        resp.raise_for_status()
        data = await resp.json()

        await session.close()
        return round(time.time() * 1000) - data['currentTime']


async def get_order_by_id(symbol, order_id):
    # this endpoint should support symbol query
    session = aiohttp.ClientSession()
    url = f"{get_domain()}/market/getOrderById?orderId={order_id}"
    async with session.get(url) as resp:
        data = await resp.json()

        await session.close()
        try:
            order = data["order"][0]
            return order
        except TypeError:
            raise Exception("Order not found")


async def get_open_orders(symbol):
    session = aiohttp.ClientSession()
    url = f"{get_domain()}/market/open-orders?symbol={symbol}"
    async with session.get(url) as resp:
        try:
            data = await resp.json()
        except (aiohttp.ContentTypeError):
            print("error", symbol)
            await session.close()
            return []

        await session.close()
        return data["openOrders"]


async def get_orders(symbol, status, start_time, end_time, limit=500, page=0):
    session = aiohttp.ClientSession()
    # waiting for back-end side implementation
    await session.close()
    pass


async def get_price(symbol):
    session = aiohttp.ClientSession()
    url = f"{get_domain()}/market/price?symbol={symbol}"
    async with session.get(url) as resp:
        data = await resp.json()
        await session.close()
        return data


async def get_depth(symbol, depth=100):
    session = aiohttp.ClientSession()
    url = f"{get_domain()}/market/depth?symbol={symbol}&depth={depth}"
    async with session.get(url) as resp:
        data = await resp.json()
        await session.close()
        return data


async def get_last_trades(symbol):
    session = aiohttp.ClientSession()
    url = f"{get_domain()}/market/last-trades?symbol={symbol}"
    async with session.get(url) as resp:
        data = await resp.json()
        await session.close()
        return data


async def get_symbols(mask) -> dict[str, str]:
    """
    Returns a list of dictionaries with matched pair keys

    Return example: [{'pairKey': 'algo_usdt'}]
    """
    session = aiohttp.ClientSession()
    url = f"{get_domain()}/market/symbols?mask={mask}"
    async with session.get(url) as resp:
        data = await resp.json()
        await session.close()
        return data


async def get_history(symbol, interval="", start_time="", end_time="", limit=""):
    session = aiohttp.ClientSession()
    url = f"{get_domain()}/market/history?symbol={symbol}&interval={interval}&startTime={start_time}&endTime={end_time}&limit={limit}"
    async with session.get(url) as resp:
        data = await resp.json()
        await session.close()
        return data


async def get_address_orders(address, status=1, symbol=None):  # is not documented
    session = aiohttp.ClientSession()
    symbol_query = f"&symbol={symbol}" if symbol else ""
    url = f"{get_domain()}/market/orders-with-trades?address={address}&status={status}{symbol_query}"
    async with session.get(url) as resp:
        data = await resp.json()
        await session.close()
        return data


async def get_wallet_transactions(address, symbol=None):  # is not documented
    session = aiohttp.ClientSession()
    symbol_query = f"&symbol={symbol}" if symbol else ""
    url = f"{get_domain()}/market/wallet-transactions?address={address}{symbol_query}"
    async with session.get(url) as resp:
        data = await resp.json()
        await session.close()
        return data


async def get_encoded_balance(address, app_id):
    session = aiohttp.ClientSession()
    url = f"https://indexer.testnet.algoexplorerapi.io/v2/accounts/{address}?include-all=true"
    async with session.get(url) as resp:
        data = await resp.json()
        await session.close()
        state = next((state for state in data["account"].get(
            'apps-local-state') if state["id"] == app_id and state["deleted"] == False), None)
        if not state:
            raise Exception(
                "An error occurred while trying to get available balance from the smart contract")

        key = next((elem for elem in state["key-value"]
                    if elem["key"] == "YWNjb3VudEluZm8="), None)
        if not key:
            raise Exception(
                "Error: can't find balance value for the specified application_id")

        return key["value"].get("bytes")
