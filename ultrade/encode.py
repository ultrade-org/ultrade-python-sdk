import eth_abi
from algosdk.encoding import decode_address
from typing import Union
from enum import Enum


class AddressType(Enum):
    EVM = 0
    Algorand = 1
    AlgorandAsset = 2
    # SolanaMint = 3


def normalize_address(address: Union[str, int], addr_type: AddressType) -> bytes:
    if addr_type == AddressType.EVM:
        return eth_abi.encode(["address"], [address])
    elif addr_type == AddressType.Algorand:
        return decode_address(address)
    elif addr_type == AddressType.AlgorandAsset:
        return eth_abi.encode(["uint256"], [int(address)])


def determine_address_type(chain_id: int, is_token: bool) -> AddressType:
    if chain_id == 5:
        return AddressType.EVM
    elif chain_id == 1:
        return AddressType.SolanaMint
    elif chain_id == 8:
        return AddressType.AlgorandAsset if is_token else AddressType.Algorand


def get_order_bytes(
    data: dict,
) -> bytes:
    order = bytearray()
    order.extend(data["expiredTime"].to_bytes(8, "big"))
    order.extend(data["orderSide"].encode())
    order.extend(eth_abi.encode(["uint256"], [data["price"]]))
    order.extend(eth_abi.encode(["uint256"], [data["amount"]]))
    order.extend(data["orderType"].encode())
    order.extend(
        normalize_address(
            data["address"], determine_address_type(data["chainId"], False)
        )
    )
    order.extend(data["chainId"].to_bytes(8, "big"))
    order.extend(
        normalize_address(
            data["baseTokenAddress"],
            determine_address_type(data["baseTokenChainId"], True),
        )
    )
    order.extend(data["baseTokenChainId"].to_bytes(8, "big"))
    order.extend(
        normalize_address(
            data["priceTokenAddress"],
            determine_address_type(data["priceTokenChainId"], True),
        )
    )
    order.extend(data["priceTokenChainId"].to_bytes(8, "big"))
    order.extend(data["wlpId"].to_bytes(8, "big"))
    return bytes(order)
