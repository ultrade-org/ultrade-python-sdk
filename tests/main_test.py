from ultrade.sdk_client import Client
from ultrade import api, Signer
from ultrade.types import ClientOptions, CreateOrder
import pprint

import pytest
from unittest.mock import patch, AsyncMock

from algosdk.v2client import algod
from algosdk import transaction

from . import utils
from .test_credentials import TEST_API_URL, TEST_MNEMONIC_KEY, TEST_COMPANY_DOMAIN


# ALGO_USDC_ORDER = {
#     "symbol": "algo_usdc",
#     "side": 'B',
#     "type": "L",
#     "quantity": 2000000,
#     "price": 800
# }

# LMBO_USDC_ORDER = {
#     "symbol": "lmbo_usdc",
#     "side": 'B',
#     "type": "L",
#     "quantity": 350000000,
#     "price": 800
# }


class TestClient:

    @classmethod
    def setup_class(cls):
        cls.client = Client(network="testnet", api_url=TEST_API_URL)
        cls.api = cls.client.create_api()

    @pytest.mark.asyncio
    async def test_create_order(self):
        company_id = await self.api.get_company_by_domain(TEST_COMPANY_DOMAIN)
        pairs = await self.api.get_pair_list(company_id)
        pair = pairs[0]
        print("PAIR", pair)
        login_user = Signer.create_signer(TEST_MNEMONIC_KEY)
        await self.client.set_login_user(login_user)
        response = await self.client.create_order(
            pair_id=pair["id"],
            company_id=company_id,
            order_side="B",
            order_type="L",
            amount=350000000,
            price=1000,
            base_token_address=pair["base_id"],
            base_token_chain_id=pair["base_chain_id"],
            price_token_address=pair["price_id"],
            price_token_chain_id=pair["price_chain_id"],
        )
        print("response", response)
        exit(0)
        create_order = CreateOrder(**create_order_data)
        
        with patch('aiohttp.ClientSession') as mock_session:
            mock_resp = AsyncMock()
            mock_resp.json.return_value = {"order_id": "123456"}
            mock_session.return_value.__aenter__.return_value.post.return_value = mock_resp
            

            await ultrade_client.set_login_user(mock_signer)

            # Вызываем метод create_order
            result = await ultrade_client.create_order(create_order)

            assert result == {"order_id": "123456"}

@pytest.mark.asyncio
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

            if len(orders) != 0:
                utils.validate_response_for_expected_fields(
                    orders[0], ["pair_id", "slot", "id"])
                return

        raise Exception("Test failed")

    async def test_get_wallet_transactions(self):
        transactions = await client.get_wallet_transactions(TEST_ALGOD_ADDRESS)
        if len(transactions) == 0:
            return

        utils.validate_response_for_expected_fields(
            transactions[0], ["txnId", "pair", "amount"])

    async def test_get_balances(self):
        data = await client.get_balances("lmbo_usdc")
        utils.validate_response_for_expected_fields(
            data, ["priceCoin_locked", "priceCoin_available", "baseCoin_locked", "baseCoin_available",
                   "priceCoin", "baseCoin"])

    async def test_get_balances_with_algo(self):
        data = await client.get_balances("algo_usdc")
        utils.validate_response_for_expected_fields(
            data, ["priceCoin_locked", "priceCoin_available", "baseCoin_locked", "baseCoin_available",
                   "priceCoin", "baseCoin"])


@pytest.mark.asyncio
class TestGetExchangeInfo():
    async def test_algo_usdc(self):
        symbol = "algo_usdc"
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
        app_id = 202953808  # algo_usdc
        balance = await api._get_encoded_balance(TEST_ALGO_WALLET, app_id)
        assert balance is not None

    async def test_get_last_trades(self):
        trades = await api.get_last_trades(TEST_SYMBOL)
        if len(trades) == 0:
            return

        utils.validate_response_for_expected_fields(
            trades[0], ["price", "amount", "buy_user_id", "sell_user_id"])
