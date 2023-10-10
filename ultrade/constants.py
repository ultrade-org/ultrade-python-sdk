
default_api_domain = "https://api.testnet.ultrade.org"
algod_indexer_url = 'https://testnet-idx.algonode.cloud'
algod_node_url = 'https://testnet-api.algonode.cloud'


def set_domains(api, algod_indexer, algod_node):
    global default_api_domain, algod_indexer_url, algod_node_url
    default_api_domain = api
    algod_indexer_url = algod_indexer
    algod_node_url = algod_node


def get_api_domain():
    return default_api_domain


def get_algod_indexer_domain():
    return algod_indexer_url


def get_algod_node_domain():
    return algod_node_url


OPEN_ORDER_STATUS = "1"

BALANCE_DECODE_FORMAT = {
    "priceCoin_locked": {
        "type": "uint",
    },
    "priceCoin_available": {
        "type": "uint",
    },
    "baseCoin_locked": {
        "type": "uint",
    },
    "baseCoin_available": {
        "type": "uint",
    },
    "WLFeeWallet": {
        "type": "address",
    },
    "WLFeeShare": {
        "type": "uint",
    },
    "WLCustomFee": {
        "type": "uint",
    },
    "slotMap": {
        "type": "uint",
    },
}

EVENT_LIST = [('quote', 1), ('last_price', 2), ('depth', 3), ('order', 5),
              ('trades', 6), ('trade', 6), ('mode', 7), ('walletTransaction', 8), ('allStat', 9)]


class OrderType():
    cancel_order = "cancel_order"
    new_order = "new_order"
