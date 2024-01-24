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


def make_withdraw_msg(
    login_address: str,
    login_chain_id: int,
    recipient: str,
    recipient_chain_id: int,
    token_amount: int,
    token_address: str,
    token_chain_id: int,
) -> bytes:
    msg = bytearray()
    token_amount_bytes = token_amount.to_bytes(32, "big")
    sender_bytes = normalize_address(
        recipient, determine_address_type(recipient_chain_id, False)
    )
    recipient_chain_id_bytes = recipient_chain_id.to_bytes(8, "big")

    box_name_bytes = get_account_balance_box_name(
        login_address, login_chain_id, token_address, token_chain_id
    )
    msg.extend(box_name_bytes)
    msg.extend(sender_bytes)
    msg.extend(recipient_chain_id_bytes)
    msg.extend(token_amount_bytes)

    message_bytes = bytes(msg)

    return message_bytes


def get_account_balance_box_name(
    login_address: str,
    login_chain_id: int,
    token_address: Union[str, int],
    token_chain_id: int,
) -> bytes:
    box_bytes = bytearray()
    address_bytes = normalize_address(
        login_address, determine_address_type(login_chain_id, False)
    )
    chain_id_bytes = login_chain_id.to_bytes(8, "big")
    token_chain_id_bytes = token_chain_id.to_bytes(8, "big")
    token_bytes = normalize_address(
        token_address, determine_address_type(token_chain_id, True)
    )
    box_bytes.extend(address_bytes)
    box_bytes.extend(chain_id_bytes)
    box_bytes.extend(token_bytes)
    box_bytes.extend(token_chain_id_bytes)
    box_name = bytes(box_bytes)
    return box_name
