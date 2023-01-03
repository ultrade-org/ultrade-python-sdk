import requests
from constants import get_domain
import time

# should be replaced when dedicated endpoint is ready
def get_exchange_info(identifier):
    data = requests.get(f"{get_domain()}/market/markets").json()
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

    raise "Can't find exchange info for the specified symbol"


def ping():
    response = requests.get(f"{get_domain()}/system/time")
    code = response.status_code
    if code != 200:
        raise "Ping request failed"
    sever_time = response.json()['currentTime']

    return round(time.time() * 1000) - sever_time


def get_order_by_id(symbol, order_id):
    # this endpoint should support symbol query
    url = f"{get_domain()}/market/getOrderById?orderId={order_id}"
    data = requests.get(url).json()
    if not len(data["order"]):
        raise "Order not found"
    return data["order"]


def get_open_orders(symbol):
    data = requests.get(
        f"{get_domain()}/market/open-orders?symbol={symbol}").json()
    return data["openOrders"]


def get_orders(symbol, start_time, end_time, limit=500, page=0):
    # waiting for back-end side implementation
    pass


def get_price(symbol):
    data = requests.get(f"{get_domain()}/market/price?symbol={symbol}").json()
    return data


def get_depth(symbol, depth):
    data = requests.get(
        f"{get_domain()}/market/depth?symbol={symbol}&depth={depth}").json()
    return data


def get_last_trades(symbol):
    data = requests.get(
        f"{get_domain()}/market/last-trades?symbol={symbol}").json()
    return data


def get_symbols(mask) -> dict[str, str]:
    """
    Returns a list of dictionaries with matched pair keys

    Return example: [{'pairKey': 'algo_usdt'}]
    """
    data = requests.get(f"{get_domain()}/market/symbols?mask={mask}").json()
    return data


def get_history(symbol, interval, start_time, end_time, limit=500):
    data = requests.get(
        f"{get_domain()}/market/history?symbol={symbol}&interval={interval}&startTime={start_time}&endTime={end_time}&limit={limit}").json()
    return data


def get_trade_orders(address, status, symbol=None):  # is not documented
    symbol_query = f"&symbol={symbol}" if symbol else ""
    data = requests.get(
        f"{get_domain()}/market/orders-with-trades?address={address}&status={status}{symbol_query}").json()
    return data


def get_wallet_transactions(address, symbol=None):  # is not documented
    symbol_query = f"&symbol={symbol}" if symbol else ""
    data = requests.get(
        f"{get_domain()}/market/wallet-transactions?address={address}{symbol_query}").json()
    return data

def get_encoded_balance(address, app_id):
        data = requests.get(
         f"https://indexer.testnet.algoexplorerapi.io/v2/accounts/{address}?include-all=true").json()
        
        state = next(state for state in data["account"].get('apps-local-state') if state["id"] == app_id and state["deleted"] == False)
        if not state:
            return
        
        key = next(elem for elem in state["key-value"] if elem["key"] == "YWNjb3VudEluZm8=")
        return key["value"].get("bytes")
