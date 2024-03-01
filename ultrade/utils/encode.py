import eth_abi
from algosdk.encoding import decode_address
from typing import Union
from enum import Enum
import base64
import json


class AddressType(Enum):
    EVM = 0
    Algorand = 1
    AlgorandAsset = 2
    SolanaMint = 3


def normalize_address(address: Union[str, int], addr_type: AddressType) -> bytes:
    if addr_type == AddressType.EVM:
        return eth_abi.encode(["address"], [address])
    elif addr_type == AddressType.Algorand:
        return decode_address(address)
    elif addr_type == AddressType.AlgorandAsset:
        return eth_abi.encode(["uint256"], [int(address)])


def determine_address_type(chain_id: int, is_token: bool) -> AddressType:
    if chain_id == 1:
        return AddressType.SolanaMint
    elif chain_id == 8:
        return AddressType.AlgorandAsset if is_token else AddressType.Algorand
    else:
        return AddressType.EVM


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

    base64_order = base64.b64encode(bytes(order))

    json_data = {
        "expiredTime": data["expiredTime"],
        "side": data["orderSide"],
        "price": data["price"],
        "amount": data["amount"],
        "type": data["orderType"],
        "loginAddress": data["address"],
        "loginChainId": data["chainId"],
        "baseTokenAddress": data["baseTokenAddress"],
        "baseTokenChainId": data["baseTokenChainId"],
        "priceTokenAddress": data["priceTokenAddress"],
        "priceTokenChainId": data["priceTokenChainId"],
        "wlpId": data["wlpId"],
    }
    json_order = json.dumps(json_data) + "\n"
    json_order_bytes = json_order.encode("utf-8")

    message_bytes = bytearray(json_order_bytes) + bytearray(base64_order)
    return bytes(message_bytes)


def make_withdraw_msg(
    login_address: str,
    login_chain_id: int,
    recipient: str,
    recipient_chain_id: int,
    token_amount: int,
    token_address: str,
    token_chain_id: int,
) -> bytes:
    data_bytes = bytearray()
    token_amount_bytes = token_amount.to_bytes(32, "big")
    sender_bytes = normalize_address(
        recipient, determine_address_type(recipient_chain_id, False)
    )

    recipient_chain_id_bytes = recipient_chain_id.to_bytes(8, "big")

    box_name_bytes = get_account_balance_box_name(
        login_address, login_chain_id, token_address, token_chain_id
    )
    data_bytes.extend(box_name_bytes)
    data_bytes.extend(sender_bytes)
    data_bytes.extend(recipient_chain_id_bytes)
    data_bytes.extend(token_amount_bytes)

    json_data = {
        "loginAddress": login_address,
        "loginChainId": login_chain_id,
        "tokenAmount": token_amount,
        "tokenIndex": token_address,
        "tokenChainId": token_chain_id,
        "recipient": recipient,
        "recipientChainId": recipient_chain_id,
    }
    json_withdraw = json.dumps(json_data, separators=(",", ":")) + "\n"
    utf8_encoded_data = json_withdraw.encode("utf-8")
    base64_encoded_data = base64.b64encode(bytes(data_bytes))
    message_bytes = bytearray(utf8_encoded_data) + bytearray(base64_encoded_data)
    return bytes(message_bytes)


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
