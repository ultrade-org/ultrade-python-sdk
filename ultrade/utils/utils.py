from typing import Dict
import re
import base64
import base58
from bip_utils import AlgorandMnemonicValidator
from ..constants import OrderType
from algosdk.encoding import is_valid_address as is_valid_algorand_address
from ..types import WormholeChains


def is_asset_opted_in(balances: Dict[str, str], asset_id: int):
    for key in balances:
        if str(key) == str(asset_id):
            return True
    return False


def is_app_opted_in(app_id: int, app_local_state):
    for a in app_local_state:
        if str(a["id"]) == str(app_id):
            return True
    return False


def construct_new_order_args(side, type, price, quantity, partnerAppId, direct_settle):
    args = [
        OrderType.new_order,
        side,
        price,
        quantity,
        type,
        partnerAppId,
        direct_settle,
    ]
    return args


def decode_txn_logs(txn_logs, order_type):
    decoded_logs = [
        int.from_bytes(base64.b64decode(log), byteorder="big") for log in txn_logs
    ]

    decoded_data = {}
    if order_type == OrderType.new_order:
        decoded_data["order_id"] = decoded_logs[1]
        decoded_data["slot"] = decoded_logs[7]
        return decoded_data

    if order_type == OrderType.cancel_order:
        decoded_data["order_id"] = decoded_logs[1]
        decoded_data["released_amount"] = decoded_logs[2]
        decoded_data["base_coin_avaliable"] = decoded_logs[3]
        decoded_data["base_coin_locked"] = decoded_logs[4]
        decoded_data["price_coin_avaliable"] = decoded_logs[5]
        decoded_data["price_coin_locked"] = decoded_logs[6]
        return decoded_data

    raise Exception("Unable to decode txn logs")


def validate_mnemonic(mnemonic):
    isMnemonicValid = AlgorandMnemonicValidator().IsValid(mnemonic)
    if isMnemonicValid:
        return

    raise Exception("invalid mnemonic phrase")


def is_valid_evm_address(address: str) -> bool:
    return re.match(r"^0x[a-fA-F0-9]{40}$", address) is not None


def is_valid_solana_address(address: str) -> bool:
    try:
        decoded = base58.b58decode(address)
        return len(decoded) == 32
    except Exception:
        return False


def get_wh_id_by_address(address: str):
    if is_valid_algorand_address(address):
        return WormholeChains.ALGORAND.value
    elif is_valid_evm_address(address):
        return WormholeChains.POLYGON.value
    elif is_valid_solana_address(address):
        return WormholeChains.SOLANA.value
    else:
        raise Exception("Invalid address")
