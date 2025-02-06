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
    },
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

EVENT_LIST = [
    ("error", 0),
    ("quote", 1),
    ("lastPrice", 2),
    ("depth", 3),
    ("order", 5),
    ("lastTrade", 6),
    ("userTrade", 6),
    ("maintenance", 7),
    ("walletTransaction", 8),
    ("allStat", 9),
    ("codexBalances", 10),
    ("lastLook", 11),
    ("codexAssets", 12),
]


CCTP_UNIFIED_ASSETS = {
    "0x4343545055534443000000000000000000000000000000000000000000000000": 65537,
}


class OrderType:
    cancel_order = "cancel_order"
    new_order = "new_order"


TMC_ABI = [
    {
        "inputs": [
            {"internalType": "address", "name": "token", "type": "address"},
            {"internalType": "uint256", "name": "amount", "type": "uint256"},
            {"internalType": "bytes", "name": "loginAddress", "type": "bytes"},
            {
                "internalType": "uint256",
                "name": "loginChainId",
                "type": "uint256",
            },
        ],
        "name": "depositToCodex",
        "outputs": [{"internalType": "uint64", "name": "sequence", "type": "uint64"}],
        "stateMutability": "nonpayable",
        "type": "function",
    }
]

ERC20_ABI = [
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function",
    },
    {
        "constant": False,
        "inputs": [
            {"name": "_to", "type": "address"},
            {"name": "_value", "type": "uint256"},
        ],
        "name": "transfer",
        "outputs": [{"name": "success", "type": "bool"}],
        "payable": False,
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "constant": False,
        "inputs": [
            {"name": "_spender", "type": "address"},
            {"name": "_value", "type": "uint256"},
        ],
        "name": "approve",
        "outputs": [{"name": "success", "type": "bool"}],
        "payable": False,
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "constant": True,
        "inputs": [
            {"name": "_owner", "type": "address"},
            {"name": "_spender", "type": "address"},
        ],
        "name": "allowance",
        "outputs": [{"name": "remaining", "type": "uint256"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function",
    },
]

DEFAULT_LOGIN_MESSAGE = "By signing this message you are logging into your trading account and agreeing to all terms and conditions of the platform."
