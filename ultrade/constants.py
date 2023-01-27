default_api_domain = "https://dev-apigw.ultradedev.net"
algod_indexer_url = 'https://indexer.testnet.algoexplorerapi.io'
algod_node_url = 'https://node.testnet.algoexplorerapi.io'


def set_domains(api, algod_indexer, algod_node):
    global default_api_domain, algod_indexer_url, algod_node_url
    default_api_domain = api
    algod_indexer_url = algod_indexer
    algod_node_url = algod_node


def get_api_domain():
    return default_api_domain


def get_algod_indexer_domain():
    return algod_indexer_url


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
