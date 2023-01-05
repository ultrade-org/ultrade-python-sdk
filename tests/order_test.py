
from ultrade.sdk_client import Client

from unittest.mock import patch
from .test_credentials import TEST_MNEMONIC_KEY, TEST_ALGOD_TOKEN, TEST_ALGOD_ADDRESS

from algosdk.v2client import algod
from algosdk import transaction

algod_client = algod.AlgodClient(TEST_ALGOD_TOKEN, TEST_ALGOD_ADDRESS)

# key = mnemonic.to_private_key(TEST_MNEMONIC_KEY)
# address = account.address_from_private_key(key)

credentials = {"mnemonic": TEST_MNEMONIC_KEY}
opts = {"network": "testnet", "algo_sdk_client": algod_client,
        "api_url": None, "websocket_url": "wss://dev-ws.ultradedev.net/socket.io"}
client = Client(credentials, opts)

ALGO_USDT_ORDER = {
    "symbol": "algo_usdt",
    "side": 'S',
    "type": "0",
    "quantity": 2000000,
    "price": 800,
    "partner_app_id": "87654321"
}

YLDY_STBL_ORDER = {
    "symbol": "yldy_stbl",
    "side": 'S',
    "type": "0",
    "quantity": 350000000,
    "price": 800,
    "partner_app_id": "87654321"
}

VIP_MYKE_ORDER = {
    "symbol": "vip_myke",
    "side": 'S',
    "type": "0",
    "quantity": 2,
    "price": 800,
    "partner_app_id": "87654321"
}


def mocked_send_transaction(self, txn_grp):
    dry_run_request = transaction.create_dryrun(self.client, txn_grp)
    data = algod_client.dryrun(dry_run_request)
    print("txn length", len(data["txns"]))
    txn = next(txn for txn in data["txns"]
               if txn.get('app-call-messages') != None)

    print("app-call-status", txn.get('app-call-messages'))
    return (txn.get('app-call-messages')[1], data["error"])


def mocked_get_order_by_id(symbol, order_id):
    return [{
        "orders_id": 53694,
        "slot": 60,
        "application_id": 92958595  # yldy_stbl
    }]


@ patch('ultrade.algod_service.AlgodService.send_transaction_grp', mocked_send_transaction)
class TestNewOrder():

    def test_yldy_sell(self):
        txn_result = client.new_order({**YLDY_STBL_ORDER, "side": "S"})
        assert txn_result == ('PASS', "")

    def test_yldy_buy(self):
        txn_result = client.new_order({**YLDY_STBL_ORDER, "side": "B"})
        assert txn_result == ('PASS', "")

    def test_yldy_with_bad_quantity(self):
        txn_result = client.new_order({**YLDY_STBL_ORDER, "quantity": 350})
        assert txn_result == ('REJECT', "")

    def test_algo_sell(self):
        txn_result = client.new_order({**ALGO_USDT_ORDER, "side": "S"})
        assert txn_result == ('PASS', "")

    def test_algo_buy(self):
        txn_result = client.new_order({**ALGO_USDT_ORDER, "side": "B"})
        assert txn_result == ('PASS', "")

    def test_vip_myke(self):
        txn_result = client.new_order(VIP_MYKE_ORDER)
        assert txn_result == ('PASS', "")


@patch('ultrade.algod_service.AlgodService.send_transaction_grp', mocked_send_transaction)
@patch('ultrade.api.get_order_by_id', mocked_get_order_by_id)
class TestCancelOrder():
    def test_yldy_stbl(self):
        example_order_id = 76735
        symbol = "yldy_stbl"

        txn_result = client.cancel_order(symbol, example_order_id)
        assert txn_result == ('PASS', "")

# ws_sub_key = ultrade_sdk.subscribe(ws_options, ws_callback)


class TestCancelAllOrders:
    pass
# 'app-call-messages', 'app-call-trace', 'budget-added', 'budget-consumed', 'disassembly', 'global-delta', 'local-deltas', 'logs'
# ultrade_sdk.new_order(symbol, order_2)
# ultrade_sdk.cancel_order("algo_usdc", 76678)
# ultrade_sdk.cancel_all_orders("algo_usdc")

# value = api.get_depth("algo_usdt", 100)
# print("value", value)
