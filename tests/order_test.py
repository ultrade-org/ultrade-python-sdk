
from . import utils
from ultrade.sdk_client import Client
from ultrade import api

from unittest.mock import patch
from .test_credentials import TEST_MNEMONIC_KEY, TEST_ALGOD_TOKEN, TEST_ALGOD_ADDRESS

from algosdk.v2client import algod
from algosdk import transaction
from pytest_mock import mocker
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
    "price": 800
}

YLDY_STBL_ORDER = {
    "symbol": "yldy_stbl",
    "side": 'S',
    "type": "0",
    "quantity": 350000000,
    "price": 800
}

VIP_MYKE_ORDER = {
    "symbol": "vip_myke",
    "side": 'S',
    "type": "0",
    "quantity": 2,
    "price": 800
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
    return {
        "orders_id": 99999,
        "slot": 50,
        "application_id": 92958595  # yldy_stbl
    }


@patch('ultrade.algod_service.AlgodService.send_transaction_grp', mocked_send_transaction)
class TestNewOrder():

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
class TestCancelOrder():
    @patch('ultrade.api.get_order_by_id', mocked_get_order_by_id)
    def test_for_non_existed_order(self):
        example_order_id = 99999
        symbol = "yldy_stbl"

        txn_result = client.cancel_order(symbol, example_order_id)
        assert txn_result == ('REJECT', "")

    def test_cancel_random_order(self):
        order = utils.find_open_order()
        if order == None:
            return

        order_id = order.get("id")
        symbol = api.get_order_by_id(None, order_id)["pair_key"]
        print("symbol", symbol)
        print(f"testing cancellation of order with id:{order_id}")

        txn_result = client.cancel_order(symbol, order_id)
        assert txn_result == ('PASS', "")


@patch('ultrade.algod_service.AlgodService.send_transaction_grp', mocked_send_transaction)
class TestCancelAllOrders:
    def test_yldy_stbl(self):
        symbol = "yldy_stbl"
        txn_result = client.cancel_all_orders(symbol)
        assert txn_result == ('PASS', "") or txn_result == None
