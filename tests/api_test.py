import pytest
from . import utils
from ultrade import api


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

    def test_get_open_orders(self):
        pass

    def test_get_orders(self):
        pass

    def test_get_price(self):
        pass

    def test_get_depth(self):
        pass

    def test_get_last_trades(self):
        pass

    def test_get_symbols(self):
        pass

    def test_get_history(self):
        pass

    def test_get_trade_orders(self):
        pass

    def test_get_wallet_transactions(self):
        pass

    def test_get_encoded_balance(self):
        pass
