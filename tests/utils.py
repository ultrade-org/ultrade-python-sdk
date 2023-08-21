from ultrade import api


async def find_open_order(client):
    order_list = await client.get_orders(status=1)
    order = order_list[0] if len(order_list) > 0 else None
    return order


async def get_symbol_of_open_order(client):
    order = await find_open_order(client)
    if not order:
        return None

    pair_info = await api._get_exchange_info_old(order["pair_id"])
    return pair_info["pair_key"]


def validate_response_for_expected_fields(res_data: dict, fields_to_check=[]):
    if not isinstance(res_data, dict):
        return

    field = None
    try:
        for f in fields_to_check:
            field = f
            res_data[f]
    except Exception:
        raise Exception(
            f"Error: field '{field}' doesn't exist in response data")
