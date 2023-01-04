from pytest_mock import mocker
from ultrade.sdk_client import Client

from .test_credentials import TEST_MNEMONIC_KEY, TEST_ALGOD_TOKEN, TEST_ALGOD_ADDRESS

from algosdk.v2client import algod
from algosdk import account, mnemonic, transaction

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


def mocked_send_transaction(self, txn_grp):
    dry_run_request = transaction.create_dryrun(self.client, txn_grp)
    data = algod_client.dryrun(dry_run_request)
    txn = data["txns"][0] if len(data["txns"]) == 1 else data["txns"][1]

    return (txn['app-call-messages'][1], data["error"])


class TestNewOrder():

    def test_yldy_sell(self, mocker):
        mocker.patch(
            'ultrade.algod_service.AlgodService.send_transaction_grp',
            mocked_send_transaction
        )
        txn_result = client.new_order({**YLDY_STBL_ORDER, "side": "S"})
        assert txn_result == ('PASS', "")

    def test_yldy_buy(self, mocker):
        mocker.patch(
            'ultrade.algod_service.AlgodService.send_transaction_grp',
            mocked_send_transaction
        )
        txn_result = client.new_order({**YLDY_STBL_ORDER, "side": "B"})
        assert txn_result == ('PASS', "")

    def test_yldy_with_bad_quantity(self, mocker):
        mocker.patch(
            'ultrade.algod_service.AlgodService.send_transaction_grp',
            mocked_send_transaction
        )
        txn_result = client.new_order({**YLDY_STBL_ORDER, "quantity": 350})
        assert txn_result == ('REJECT', "")

    def test_algo_sell(self, mocker):
        mocker.patch(
            'ultrade.algod_service.AlgodService.send_transaction_grp',
            mocked_send_transaction
        )
        txn_result = client.new_order({**ALGO_USDT_ORDER, "side": "S"})
        assert txn_result == ('PASS', "")

    def test_algo_buy(self, mocker):
        mocker.patch(
            'ultrade.algod_service.AlgodService.send_transaction_grp',
            mocked_send_transaction
        )
        txn_result = client.new_order({**ALGO_USDT_ORDER, "side": "B"})
        assert txn_result == ('PASS', "")


# class TestCancelOrder():
#     def test_cancel(self, mocker):
#         mocker.patch(
#             'ultrade.algod_service.AlgodService.send_transaction_grp',
#             mocked_send_transaction
#         )

#         example_order_id = "SDODRM6GMMPVVWJNYCAIXV7W3EGGOJ3V5PL7XJUKHLDDTQIYG6SA"
#         symbol = "yldy_stbl"

#         txn_result = client.cancel_order(symbol, example_order_id)
#         assert txn_result == ('PASS', "")

    # ws_sub_key = ultrade_sdk.subscribe(ws_options, ws_callback)


class TestCancelAllOrders:
    pass
# 'app-call-messages', 'app-call-trace', 'budget-added', 'budget-consumed', 'disassembly', 'global-delta', 'local-deltas', 'logs'
# ultrade_sdk.new_order(symbol, order_2)
# ultrade_sdk.cancel_order("algo_usdc", 76678)
# ultrade_sdk.cancel_all_orders("algo_usdc")

# value = api.get_depth("algo_usdt", 100)
# print("value", value)
