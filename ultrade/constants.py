def get_domain():
    return "https://dev-apigw.ultradedev.net"

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