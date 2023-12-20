from eth_utils import to_bytes, to_int
from algosdk import encoding
from .types import WormholeChains

def encode(value, encode_type, chain=None):
    print(f'encode: value={value}, type={encode_type}, chain={chain}')

    if encode_type == '8B':
        return encoding.encode_uint64(int(value))
    elif encode_type == '32B':
        return encode_32_bytes(value)
    elif encode_type == 'str':
        return encode_string(value)
    elif encode_type == 'address':
        return encode_address(value, chain)
    elif encode_type == 'token':
        return encode_token(value, chain)
    else:
        return bytes(str(value), 'utf-8')

def encode_32_bytes(value):
    value_bn = to_int(hexstr=str(value))
    return to_bytes(value_bn, length=32)

def encode_string(value):
    return bytes(str(value), 'utf-8')

def encode_token(token, chain):
    if chain == WormholeChains.ALGORAND:
        return encode_32_bytes(token)
    else:
        return encode_eth_address(str(token)) 

def encode_address(address: str, chain: int) -> bytes:
    if chain == WormholeChains.Algorand:
        return encode_algo_address(address)
    else:
        return encode_eth_address(address)

def encode_algo_address(address: str) -> bytes:
    return encoding.decode_address(address)

def encode_eth_address(address: str) -> bytes:
    if address.startswith('0x'):
        address = address[2:]

    address_bytes = to_bytes(hexstr=address)
    padded_address = address_bytes.rjust(32, b'\0')

    return padded_address

def make_create_order_msg(data):
    message_bytes = b''.join([
        encode(data['expiredTime'], "8B"),
        encode(data['orderSide'], "str"),
        encode(data['price'], "32B"),
        encode(data['amount'], "32B"),
        encode(data['orderType'], "str"),
        encode(data['address'], "address", data['chainId']),
        encode(data['chainId'], "8B"),
        encode(data['baseTokenAddress'], "token", data['baseTokenChainId']),
        encode(data['baseTokenChainId'], "8B"),
        encode(data['priceTokenAddress'], "token", data['priceTokenChainId']),
        encode(data['priceTokenChainId'], "8B"),
        encode(data['wlpId'], "8B"),
    ])

    print('Order message should be 202 bytes', len(message_bytes))
    return message_bytes