from ultrade import api
from .test_credentials import TEST_ALGO_WALLET


def find_open_order():
    order_list = api.get_trade_orders(TEST_ALGO_WALLET, status=1)
    order = order_list[0] if len(order_list) > 0 else None
    return order


def validate_response_for_expected_fields(res_data, fields_to_check=[]):
    if not isinstance(res_data, dict):
        return

    field = None
    try:
        for f in fields_to_check:
            field = f
            res_data[f]
    except:
        raise f"Error: field '{field}' not exist in response data"
