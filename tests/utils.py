from ultrade import api
from .test_credentials import TEST_ALGO_WALLET


async def find_open_order(client):
    order_list = await client.get_orders(status=1)
    order = order_list[0] if len(order_list) > 0 else None
    return order


async def get_symbol_of_open_order(client):
    order = await find_open_order(client)
    if not order:
        return None

    pair_info = await api.get_exchange_info(order["pair_id"])
    print("pair key:", pair_info["pair_key"])
    return pair_info["pair_key"]


def validate_response_for_expected_fields(res_data: dict, fields_to_check=[]):
    if not isinstance(res_data, dict):
        return

    field = None
    try:
        for f in fields_to_check:
            field = f
            res_data[f]
    except:
        raise Exception(
            f"Error: field '{field}' doesn't exist in response data")
