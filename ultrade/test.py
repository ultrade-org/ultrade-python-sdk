from test_credentials import TEST_MNEMONIC_KEY, TEST_ALGOD_TOKEN, TEST_ALGOD_ADDRESS
from ultrade_sdk import Client

import algod_service
from algosdk.v2client import algod
from algosdk import account, mnemonic

key = mnemonic.to_private_key(TEST_MNEMONIC_KEY)
address = account.address_from_private_key(key)

algod_client = algod.AlgodClient(TEST_ALGOD_TOKEN, TEST_ALGOD_ADDRESS)

ws_sub_key = None
creds = {"mnemonic": TEST_MNEMONIC_KEY}
opts = {"network": "testnet", "algo_sdk_client": algod_client, "api_url": None, "websocket_url": "wss://dev-ws.ultradedev.net/socket.io"}

ultrade_sdk = Client(creds, opts)

ws_options = {
  'symbol': "yldy_stbl",
  'streams': [5,6,7],
  'options': {"address": "47HZBXMZ4V34L4ONFGQESWJYVSDVIRSZPBQM3B7WUZZXZ2622EXXXO6GSU", "partnerId": "12345678"}
}

def ws_callback(event, args):   
    if event == "allStat":
        return
    print("ws_sub_key", ws_sub_key)
    if ws_sub_key != None:
        ultrade_sdk.unsubscribe(ws_sub_key)

    print("event", event, str(args))
    
order_1 = {  # algo-usdt
    "side": 'S',
    "type": "0",
    "quantity": 2000000,
    "price": 800,
    "transfer_amount": 2000000,
    "partner_app_id": "87654321"
}

order_2 = {
    # YLDY_STBL
    "side": 'S',
    "type": "0",
    "quantity": 350000000,
    "price": 800,
    "transfer_amount": 350000000,
    "partner_app_id": "87654321"
}

# "transfer_amount": 2000000,

example_order_id = "SDODRM6GMMPVVWJNYCAIXV7W3EGGOJ3V5PL7XJUKHLDDTQIYG6SA"
symbol = "YLDY_STBL"


#ultrade_sdk.new_order(symbol, order_2)
#ultrade_sdk.cancel_order("algo_usdc", 76678)
#ultrade_sdk.cancel_all_orders("algo_usdc")

#value = api.get_depth("algo_usdt", 100)
#print("value", value)

ws_sub_key = ultrade_sdk.subscribe(ws_options, ws_callback)