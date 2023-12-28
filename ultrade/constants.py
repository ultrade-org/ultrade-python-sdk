NETWORK_CONSTANTS = {
    "testnet": {
        "api_url": "https://api.testnet.ultrade.org",
        "indexer": "https://testnet-idx.algonode.cloud",
        "node": "https://testnet-api.algonode.cloud",
        "websocket_url": "wss://ws.testnet.ultrade.org",
    },
    "mainnet": {
        "api_url": "https://api.ultrade.org",
        "indexer": "https://mainnet-idx.algonode.cloud",
        "node": "https://mainnet-api.algonode.cloud",
        "websocket_url": "wss://ws.mainnet.ultrade.org",
    }
}

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
              ('trades', 6), ('trade', 6), ('mode', 7), ('walletTransaction', 8), ('allStat', 9), ('codexBalances', 10), ('lastLook', 11), ('codexAssets', 12)]


class OrderType():
    cancel_order = "cancel_order"
    new_order = "new_order"
