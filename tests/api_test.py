import pytest
from . import utils
from ultrade import api
from .test_credentials import TEST_ALGO_WALLET, TEST_SYMBOL, TEST_ALGOD_ADDRESS


class TestGetExchangeInfo():
    def test_yldy_stbl(self):
        symbol = "yldy_stbl"
        data = api.get_exchange_info(symbol)
        utils.validate_response_for_expected_fields(
            data, ["id", "application_id", "pair_key", "base_id"])

    def test_with_wrong_symbol(self):
        symbol = "test_test123"
        with pytest.raises(Exception):
            api.get_exchange_info(symbol)


class TestApi():
    def test_ping(self):
        latency = api.ping()
        assert latency < 100_000_000

    def test_get_order_by_id(self):
        order = utils.find_open_order()
        if not order:
            return

        order_by_id = api.get_order_by_id(None, order["id"])
        utils.validate_response_for_expected_fields(order_by_id, ["pair_key"])

    # def test_get_open_orders(self):
    #     api.get_open_orders()

    # def test_get_orders(self):
    #     api.get_orders()

    def test_get_history(self):
        # api.get_history()
        pass

    def test_get_price(self):
        # symbol = utils.get_symbol_of_open_order()
        # price = api.get_price(symbol)
        # assert isinstance(price, dict) endpoint is not working
        pass

    def test_get_depth(self):
        symbol = utils.get_symbol_of_open_order()
        depth = api.get_depth(symbol)
        utils.validate_response_for_expected_fields(depth, ["buy", "sell"])

    def test_get_last_trades(self):
        trades = api.get_last_trades(TEST_SYMBOL)
        if len(trades) == 0:
            return

        utils.validate_response_for_expected_fields(
            trades[0], ["price", "amount", "buy_user_id", "sell_user_id"])

    def test_get_symbols(self):
        mask = "algo"
        symbols_list = api.get_symbols(mask)
        assert len(symbols_list) > 0

    def test_get_trade_orders(self):
        orders = api.get_trade_orders(TEST_ALGOD_ADDRESS)
        if len(orders) == 0:
            return

        utils.validate_response_for_expected_fields(
            orders[0], ["pair_id", "slot", "id"])

    def test_get_wallet_transactions(self):
        transactions = api.get_wallet_transactions(TEST_ALGOD_ADDRESS)
        if len(transactions) == 0:
            return

        utils.validate_response_for_expected_fields(
            transactions[0], ["txnId", "pair", "amount"])

    def test_get_encoded_balance(self):
        app_id = 92958595  # yldy_stbl
        balance = api.get_encoded_balance(TEST_ALGO_WALLET, app_id)
        assert balance != None
