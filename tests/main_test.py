from ultrade.sdk_client import Client
from ultrade import api

import pytest
from unittest.mock import patch

from algosdk.v2client import algod
from algosdk import transaction

from . import utils
from .test_credentials import TEST_MNEMONIC_KEY, TEST_ALGOD_TOKEN, TEST_ALGOD_ADDRESS, TEST_SYMBOL, TEST_ALGO_WALLET

algod_client = algod.AlgodClient(TEST_ALGOD_TOKEN, TEST_ALGOD_ADDRESS)

credentials = {"mnemonic": TEST_MNEMONIC_KEY}
opts = {"network": "dev", "algo_sdk_client": algod_client,
        "api_url": None, "websocket_url": "wss://dev-ws.ultradedev.net/socket.io"}
client = Client(credentials, opts)

ALGO_USDT_ORDER = {
    "symbol": "algo_usdt",
    "side": 'B',
    "type": "L",
    "quantity": 2000000,
    "price": 800
}

YLDY_STBL_ORDER = {
    "symbol": "yldy_stbl",
    "side": 'B',
    "type": "L",
    "quantity": 350000000,
    "price": 800
}

VIP_MYKE_ORDER = {
    "symbol": "vip_myke",
    "side": 'S',
    "type": "L",
    "quantity": L,
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


def mocked_wait_for_transaction(self, txn_id):
    return {"logs": txn_id}


def mocked_decode_txn_logs(logs):
    return logs


@pytest.mark.asyncio
@patch('ultrade.algod_service.AlgodService.send_transaction_grp', mocked_send_transaction)
@patch('ultrade.algod_service.AlgodService.wait_for_transaction', mocked_wait_for_transaction)
@patch('ultrade.sdk_client.decode_txn_logs', mocked_decode_txn_logs)
class TestNewOrder():

    async def test_yldy_buy(self):
        txn_result = await client.new_order(**YLDY_STBL_ORDER)
        assert txn_result == ('PASS', "")

    async def test_yldy_with_bad_quantity(self):
        txn_result = await client.new_order(**{**YLDY_STBL_ORDER, "quantity": 350})
        assert txn_result == ('REJECT', "")

    async def test_algo_sell(self):
        txn_result = await client.new_order(**{**ALGO_USDT_ORDER, "side": "S"})
        assert txn_result == ('PASS', "")

    async def test_algo_buy(self):
        txn_result = await client.new_order(**ALGO_USDT_ORDER)
        assert txn_result == ('PASS', "")

    async def test_vip_myke(self):
        txn_result = await client.new_order(**VIP_MYKE_ORDER)
        assert txn_result == ('PASS', "")


@ pytest.mark.asyncio
@ patch('ultrade.algod_service.AlgodService.send_transaction_grp', mocked_send_transaction)
class TestCancelOrder():
    async def test_for_non_existed_order(self):
        example_order_id = 99999
        example_slot = 99
        symbol = "yldy_stbl"

        txn_result = await client.cancel_order(symbol, example_order_id, example_slot)
        assert txn_result == ('REJECT', "")

    async def test_cancel_random_order(self):
        order = await utils.find_open_order(client)
        if order == None:
            return

        order_id = order.get("id")
        order = await client.get_order_by_id(None, order_id)
        print("symbol", order["pair_key"])
        print(f"testing cancellation of order with id:{order_id}")

        txn_result = await client.cancel_order(order["pair_key"], order["orders_id"], order["slot"])
        assert txn_result == ('PASS', "")


@ pytest.mark.asyncio
@ patch('ultrade.algod_service.AlgodService.send_transaction_grp', mocked_send_transaction)
class TestCancelAllOrders():
    async def test_yldy_stbl(self):
        symbol = "yldy_stbl"
        txn_result = await client.cancel_all_orders(symbol)
        assert txn_result == ('PASS', "") or txn_result == None


@ pytest.mark.asyncio
class TestApiCalls():
    async def test_get_order_by_id(self):
        order = await utils.find_open_order(client)
        if not order:
            return

        order_by_id = await client.get_order_by_id(None, order["id"])
        utils.validate_response_for_expected_fields(order_by_id, ["pair_key"])

    async def test_get_orders(self):
        symbols = await api.get_symbols("")

        for s in symbols:
            orders = await client.get_orders(s["pairKey"], status=1)
            print("open", orders)
            if len(orders) != 0:
                utils.validate_response_for_expected_fields(
                    orders[0], ["pair_id", "slot", "id"])
                return

        raise Exception("Test failed")

    async def test_get_orders(self):
        orders = await client.get_orders()
        if len(orders) == 0:
            return

        utils.validate_response_for_expected_fields(
            orders[0], ["pair_id", "slot", "id"])

    async def test_get_wallet_transactions(self):
        transactions = await client.get_wallet_transactions(TEST_ALGOD_ADDRESS)
        if len(transactions) == 0:
            return

        utils.validate_response_for_expected_fields(
            transactions[0], ["txnId", "pair", "amount"])

    async def test_get_balances(self):
        data = await client.get_balances("yldy_stbl")
        utils.validate_response_for_expected_fields(
            data, ["priceCoin_locked", "priceCoin_available", "baseCoin_locked", "baseCoin_available", "priceCoin", "baseCoin"])

    async def test_get_balances_with_algo(self):
        data = await client.get_balances("algo_usdc")
        utils.validate_response_for_expected_fields(
            data, ["priceCoin_locked", "priceCoin_available", "baseCoin_locked", "baseCoin_available", "priceCoin", "baseCoin"])


@pytest.mark.asyncio
class TestGetExchangeInfo():
    async def test_yldy_stbl(self):
        symbol = "yldy_stbl"
        data = await api.get_exchange_info(symbol)
        utils.validate_response_for_expected_fields(
            data, ["id", "application_id", "pair_key", "base_id"])

    async def test_with_wrong_symbol(self):
        symbol = "test_test123"
        with pytest.raises(Exception):
            await api.get_exchange_info(symbol)


@pytest.mark.asyncio
class TestApi():
    async def test_ping(self):
        latency = await api.ping()
        assert type(latency) == int

    async def test_get_history(self):
        history = await api.get_history(TEST_SYMBOL)
        print("history", history)
        utils.validate_response_for_expected_fields(
            history[0] if len(history) > 0 else [], ["v", "o", "c", "h", "l"])

    async def test_get_price(self):
        symbol = await utils.get_symbol_of_open_order(client)
        price = await api.get_price(symbol)
        utils.validate_response_for_expected_fields(
            price, ["last", "bid", "ask"])

    async def test_get_depth(self):
        symbol = await utils.get_symbol_of_open_order(client)
        depth = await api.get_depth(symbol)
        utils.validate_response_for_expected_fields(depth, ["buy", "sell"])

    async def test_get_symbols(self):
        mask = "algo"
        symbols_list = await api.get_symbols(mask)
        assert len(symbols_list) > 0

    async def test_get_encoded_balance(self):
        app_id = 92958595  # yldy_stbl
        balance = await api._get_encoded_balance(TEST_ALGO_WALLET, app_id)
        assert balance != None

    async def test_get_last_trades(self):
        trades = await api.get_last_trades(TEST_SYMBOL)
        if len(trades) == 0:
            return

        utils.validate_response_for_expected_fields(
            trades[0], ["price", "amount", "buy_user_id", "sell_user_id"])
