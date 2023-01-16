default_domain = "https://dev-apigw.ultradedev.net"


def set_domain(domain):
    global default_domain
    default_domain = domain


def get_domain():
    return default_domain


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
