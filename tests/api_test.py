import pytest
from ultrade import api

from .test_credentials import TEST_ALGO_WALLET, TEST_SYMBOL, TEST_ALGOD_ADDRESS
from . import utils


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
        assert latency < 100_000_000

    async def test_get_order_by_id(self):
        order = await utils.find_open_order()
        if not order:
            return

        order_by_id = await api.get_order_by_id(None, order["id"])
        utils.validate_response_for_expected_fields(order_by_id, ["pair_key"])

    async def test_get_open_orders(self):
        symbols = await api.get_symbols("")
        print("symbols", symbols)
        for s in symbols:
            orders = await api.get_open_orders(s["pairKey"])
            print("open", orders)
            if len(orders) != 0:
                utils.validate_response_for_expected_fields(orders[0], [])
                return

        raise Exception("Test failed")

    async def test_get_orders(self):
        # waiting for implementation on the back-end
        pass

    async def test_get_history(self):
        # waiting for endpoint update
        history = await api.get_history(TEST_SYMBOL)
        pass

    async def test_get_price(self):
        symbol = await utils.get_symbol_of_open_order()
        price = await api.get_price(symbol)
        utils.validate_response_for_expected_fields(
            price, ["last", "bid", "ask"])

    async def test_get_depth(self):
        symbol = await utils.get_symbol_of_open_order()
        depth = await api.get_depth(symbol)
        utils.validate_response_for_expected_fields(depth, ["buy", "sell"])

    async def test_get_last_trades(self):
        trades = await api.get_last_trades(TEST_SYMBOL)
        if len(trades) == 0:
            return

        utils.validate_response_for_expected_fields(
            trades[0], ["price", "amount", "buy_user_id", "sell_user_id"])

    async def test_get_symbols(self):
        mask = "algo"
        symbols_list = await api.get_symbols(mask)
        assert len(symbols_list) > 0

    async def test_get_address_orders(self):
        orders = await api.get_address_orders(TEST_ALGOD_ADDRESS)
        if len(orders) == 0:
            return

        utils.validate_response_for_expected_fields(
            orders[0], ["pair_id", "slot", "id"])

    async def test_get_wallet_transactions(self):
        transactions = await api.get_wallet_transactions(TEST_ALGOD_ADDRESS)
        if len(transactions) == 0:
            return

        utils.validate_response_for_expected_fields(
            transactions[0], ["txnId", "pair", "amount"])

    async def test_get_encoded_balance(self):
        app_id = 92958595  # yldy_stbl
        balance = await api._get_encoded_balance(TEST_ALGO_WALLET, app_id)
        assert balance != None
