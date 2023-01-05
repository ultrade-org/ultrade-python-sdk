from ultrade import api
from test_credentials import TEST_ALGO_WALLET


def find_open_order():
    order_list = api.get_trade_orders(TEST_ALGO_WALLET, status=1)
    order = order_list[0] if len(order_list) > 0 else None
    return order
