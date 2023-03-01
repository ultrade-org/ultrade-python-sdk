from typing import Dict, List
import base64


def is_asset_opted_in(balances: Dict[str, str], asset_id: int):
    for key in balances:
        if str(key) == str(asset_id):
            print(f"asset {asset_id} is opted in")
            return True
    print(f"asset {asset_id} is not opted in")
    return False


def is_app_opted_in(app_id: int, app_local_state):
    for a in app_local_state:
        if str(a['id']) == str(app_id):
            print("app is opted in")
            return True
    print("app is not opted in")
    return False


def construct_args_for_app_call(side, type, price, quantity, partnerAppId):
    args = ["new_order", side, price, quantity, type, partnerAppId]
    return args


def construct_query_string_for_api_request(args: List):
    query_result = "?"
    for key in args:
        if key == "self":
            pass
        elif args[key] != None:
            query_result = query_result + f"{key}={args[key]}&"

    return query_result


def decode_txn_logs(txn_logs):
    decoded_logs = [int.from_bytes(base64.b64decode(
        log), byteorder='big') for log in txn_logs]

    if len(decoded_logs) < 8:
        raise Exception("Unable to decode txn logs")

    decoded_data = {}

    decoded_data["order_id"] = decoded_logs[1]
    decoded_data["slot"] = decoded_logs[7]
    return decoded_data
