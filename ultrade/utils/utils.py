import re
import base58
import json
from algosdk.encoding import is_valid_address as is_valid_algorand_address
from ..types import WormholeChains


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


def toJson(data):
    return json.dumps(data, separators=(",", ":"))
