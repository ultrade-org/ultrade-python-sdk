import eth_abi
import codecs
from algosdk.encoding import decode_address
from base58 import b58decode
from typing import Union
from os import urandom
from enum import Enum
import base64
import random
import struct

from spl.token.constants import TOKEN_PROGRAM_ID, ASSOCIATED_TOKEN_PROGRAM_ID
from spl.token.instructions import get_associated_token_address
from solders.pubkey import Pubkey

from ultrade.types import WormholeChains
from ultrade.constants import CCTP_UNIFIED_ASSETS
from .utils import toJson


class AddressType(Enum):
    EVM = 0
    Algorand = 1
    AlgorandAsset = 2
    SolanaMint = 3
    Cctp = 4
    SolanaCctp = 5


def normalize_address(address: Union[str, int], addr_type: AddressType) -> bytes:
    if addr_type == AddressType.EVM:
        return eth_abi.encode(["address"], [address])
    elif addr_type == AddressType.Algorand:
        return decode_address(address)
    elif addr_type == AddressType.AlgorandAsset:
        return eth_abi.encode(["uint256"], [int(address)])
    elif addr_type == AddressType.SolanaMint:
        return b58decode(address)
    elif addr_type == AddressType.Cctp:
        return decode_hex_string(str(address))


def determine_address_type(
    chain_id: int, is_token: bool, token: str | int = None
) -> AddressType:
    if chain_id == WormholeChains.SOLANA.value:
        if token in CCTP_UNIFIED_ASSETS:
            return AddressType.SolanaCctp
        return AddressType.SolanaMint
    elif chain_id == WormholeChains.ALGORAND.value:
        return AddressType.AlgorandAsset if is_token else AddressType.Algorand
    elif token in CCTP_UNIFIED_ASSETS:
        return AddressType.Cctp
    else:
        return AddressType.EVM


def generate_random_8bytes() -> bytes:
    max_safe_integer = 9007199254740991
    random_number = random.randint(0, max_safe_integer)
    byte_data = struct.pack('>Q', random_number)
    return byte_data


def decode32_bytes(value: str) -> bytes:
    decoded_bytes = base64.b32decode(value)
    return decoded_bytes


def decode_hex_string(address):
    if address.startswith("0x"):
        address = address[2:]
    return codecs.decode(address, "hex")


def encode_32_bytes(value: bytes) -> bytes:
    if len(value) > 32:
        raise ValueError("Value is too large to encode in 32 bytes")

    return value.rjust(32, b"\x00")


def get_utf8_encoded_data(json_data):
    return (json_data + "\n").encode("utf-8")


def make_signing_message(json_data, data):
    return get_utf8_encoded_data(json_data) + base64.b64encode(data)


def get_order_bytes(
    data: dict,
) -> bytes:
    order = bytearray()
    order.extend(data["version"].to_bytes(2, "big"))
    order.extend(data["expiredTime"].to_bytes(4, "big"))
    order.extend(data["orderSide"].encode())
    order.extend(eth_abi.encode(["uint256"], [data["price"]]))
    order.extend(eth_abi.encode(["uint256"], [data["amount"]]))
    order.extend(data["orderType"].encode())
    order.extend(
        normalize_address(
            data["address"], determine_address_type(data["chainId"], False)
        )
    )
    order.extend(data["chainId"].to_bytes(2, "big"))
    order.extend(
        normalize_address(
            data["baseTokenAddress"],
            determine_address_type(
                data["baseTokenChainId"], True, data["baseTokenAddress"]
            ),
        )
    )
    order.extend(data["baseTokenChainId"].to_bytes(4, "big"))
    order.extend(
        normalize_address(
            data["priceTokenAddress"],
            determine_address_type(
                data["priceTokenChainId"], True, data["priceTokenAddress"]
            ),
        )
    )
    order.extend(data["priceTokenChainId"].to_bytes(4, "big"))
    order.extend(data["companyId"].to_bytes(2, "big"))
    random_8bytes = generate_random_8bytes()
    order.extend(random_8bytes)
    order.extend(struct.pack('>d', data["decimalPrice"]))
    order.extend(b'\x00' * 50)

    base64_order = base64.b64encode(bytes(order))
    message_bytes = bytearray(base64_order)

    return bytes(message_bytes)


def make_withdraw_msg(
    login_address: str,
    login_chain_id: int,
    recipient: str,
    recipient_chain_id: int,
    token_amount: int,
    token_address: str,
    is_native_token: bool,
    fee: int,
    data: dict = None,
) -> bytes:
    data_bytes = bytearray()
    token_amount_bytes = token_amount.to_bytes(32, "big")

    if determine_address_type(recipient_chain_id, False, token_address) == AddressType.SolanaCctp:
        SOLANA_USDC = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v" if True == "MainNet" else "4zMMC9srt5Ri5X14GAgXhaHii3GnPAEERYPJgZJDncDU"
        USDC_MINT = Pubkey.from_string(SOLANA_USDC)

        recipient_pubkey = Pubkey.from_string(recipient)
        associated_token_address = get_associated_token_address(
            owner=recipient_pubkey,
            mint=USDC_MINT
        )

        recipient_address_bytes = normalize_address(
            str(associated_token_address), determine_address_type(recipient_chain_id, False)
        )
    else:
        recipient_address_bytes = normalize_address(
            recipient, determine_address_type(recipient_chain_id, False)
        )

    recipient_chain_id_bytes = recipient_chain_id.to_bytes(8, "big")

    fee_bytes = fee.to_bytes(32, "big")
    is_native_token_bytes = is_native_token.to_bytes(1, "big")

    box_name_bytes = get_account_balance_box_name(
        login_address, login_chain_id, token_address, recipient_chain_id
    )

    json_data = toJson(data)

    data_bytes.extend(box_name_bytes)
    data_bytes.extend(recipient_address_bytes)
    data_bytes.extend(recipient_chain_id_bytes)
    data_bytes.extend(token_amount_bytes)
    data_bytes.extend(is_native_token_bytes)
    data_bytes.extend(fee_bytes)

    message_bytes = make_signing_message(json_data, data_bytes)
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
    token_bytes = normalize_address(
        token_address, determine_address_type(token_chain_id, True)
    )
    box_bytes.extend(address_bytes)
    box_bytes.extend(chain_id_bytes)
    box_bytes.extend(token_bytes)
    box_name = bytes(box_bytes)
    return box_name
