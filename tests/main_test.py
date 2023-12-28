import asyncio
from ultrade.sdk_client import Client
from ultrade.types import OrderStatus
import pytest
from .test_credentials import TEST_API_URL, TEST_WALLET_ADDRESS

@pytest.mark.asyncio
class TestClient:

    @pytest.mark.asyncio
    async def test_get_balances(self, client_class_scope):
        print("client_class_scope", client_class_scope)
        client_instance, api_instance = client_class_scope
        balances = await client_instance.get_balances()
        assert isinstance(balances, list)
        assert all(isinstance(balance, dict) for balance in balances)

    async def test_get_orders(self, client_class_scope):
        client_instance, api_instance = client_class_scope
        orders = await client_instance.get_orders_with_trades(
            status=OrderStatus.OPEN_ORDER
        )
        assert isinstance(orders, list)
        assert all(isinstance(order, dict) for order in orders)

    async def test_create_order(self, client_class_scope):
        client_instance, api_instance = client_class_scope
        pairs = await api_instance.get_pair_list()
        pair = pairs[0]
        res = await client_instance.create_order(
            pair_id=pair["id"],
            company_id=1,
            order_side="B",
            order_type="L",
            amount=350000000,
            price=1000,
            base_token_address=pair["base_id"],
            base_token_chain_id=pair["base_chain_id"],
            price_token_address=pair["price_id"],
            price_token_chain_id=pair["price_chain_id"],
        )
        assert res == "Order created successfully"

    @pytest.mark.asyncio
    async def test_cancel_order(self, client_class_scope):
        client_instance, api_instance = client_class_scope
        orders = await client_instance.get_orders_with_trades(
            status=OrderStatus.OPEN_ORDER
        )
        order = orders[0]
        res = await client_instance.cancel_order(order["id"])
        assert res == "Order cancelled successfully"


@pytest.mark.asyncio
class TestApiCalls:
    @classmethod
    def setup_class(cls):
        cls.client = Client(network="testnet", api_url=TEST_API_URL)
        cls.api = cls.client.create_api()

    async def test_get_pair_list(self):
        company_id = 1
        pairs = await self.api.get_pair_list(company_id)
        print("pairs", pairs)
        assert isinstance(pairs, list)
        assert all(isinstance(pair, dict) for pair in pairs)

    async def test_get_exchange_info(self):
        symbol = "algo_usdc"
        exchange_info = await self.api.get_exchange_info(symbol)
        print("exchange_info", exchange_info)
        assert isinstance(exchange_info, dict)

    async def test_ping(self):
        latency = await self.api.ping()
        assert isinstance(latency, int)

    async def test_get_price(self):
        symbol = "algo_usdt"
        price_info = await self.api.get_price(symbol)
        print("price_info", price_info)
        assert isinstance(price_info, dict)

    async def test_get_depth(self):
        symbol = "algo_usdt"
        depth = 100
        depth_info = await self.api.get_depth(symbol, depth)
        print("depth_info", depth_info)
        assert isinstance(depth_info, dict)

    async def test_get_symbols(self):
        mask = "algo"
        symbols = await self.api.get_symbols(mask)
        print("Symbols:", symbols)
        assert isinstance(symbols, list)
        assert all(isinstance(symbol, dict) for symbol in symbols)
        assert all(mask in symbol["pairKey"] for symbol in symbols)

    async def test_get_history(self):
        symbol = "moon_algo"
        interval = "1h"
        history = await self.api.get_history(symbol, interval)
        print(
            "History for symbol:",
            symbol,
            "Interval:",
            interval,
            "History Data:",
            history,
        )
        assert isinstance(history, dict)

    async def test_get_last_trades(self):
        symbol = "moon_algo"
        last_trades = await self.api.get_last_trades(symbol)
        print("Last trades for symbol:", symbol, "Trades Data:", last_trades)
        assert isinstance(last_trades, list)

    # async def test_get_orders(self):
    #     status = 1  # Open orders
    #     orders = await self.api.get_orders(status, address="")
    #     print("Orders Data:", orders)
    #     assert isinstance(orders, list)

    async def test_get_order_by_id(self):
        order_id = 1
        order_data = await self.api.get_order_by_id(order_id)
        print("Order data for order_id:", order_id, "Order Data:", order_data)
        assert isinstance(order_data, dict)

@pytest.mark.asyncio
class TestSocket:
    async def test_socket(self, client_class_scope):
        client_instance, api_instance = client_class_scope
        received_event = asyncio.Event()
        received_data = None
        subscribe_options = {
            "symbol": "",
            "streams": [1, 2, 3, 5, 6, 7, 8, 9, 10, 11],
            "options": {
                "address": TEST_WALLET_ADDRESS
            }
        }
        def callback(event, data):
            nonlocal received_data
            print("event", event)
            print("data", data)
            received_data = data
            received_event.set()
        
        sub_id = await client_instance.subscribe(subscribe_options, callback)
        print("sub_id", sub_id)

        await received_event.wait()
        assert received_data is not None
        assert isinstance(received_data, list)
        assert all(isinstance(data, dict) for data in received_data)
        await client_instance.unsubscribe(sub_id)