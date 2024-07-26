import asyncio
from ultrade.sdk_client import Client, Signer
from ultrade.types import OrderStatus
import pytest
from .test_credentials import (
    TEST_API_URL,
    TEST_ETH_PRIVATE_KEY,
    TEST_MNEMONIC_KEY,
    TEST_WALLET_ADDRESS,
    TEST_WITHDRAW,
    TEST_PAIR_NAME,
)


@pytest.mark.asyncio
class TestClient:
    @pytest.mark.asyncio
    async def test_get_balances(self, client):
        balances = await client.get_balances()
        print("Balances:", balances)
        assert isinstance(balances, list)
        assert all(isinstance(balance, dict) for balance in balances)

    async def test_get_orders_with_trades(self, client):
        orders = await client.get_orders_with_trades(status=OrderStatus.OPEN_ORDER)
        print("orders", orders)
        assert isinstance(orders, list)
        assert all(isinstance(order, dict) for order in orders)

    async def test_rate_limit(self, client):
        count = 0
        try:
            for i in range(1000):
                client.get_balances()
                count = i
        except Exception as e:
            print("Exception:", e)
        print("Count:", count)

    async def test_create_order(self, client):
        pair = await client.get_pair_info(TEST_PAIR_NAME)
        print("Pair:", pair)
        res = await client.create_order(
            pair_id=pair["id"],
            order_side="S",
            order_type="L",
            amount=100000000000000000,
            price=2000,
        )
        print("Order:", res)

    async def test_create_order_with_insufficient_balance(self, client):
        pairs = await client.get_pair_list()
        pair = pairs[0]
        try:
            res = await client.create_order(
                pair_id=pair["id"],
                order_side="S",
                order_type="L",
                amount=450000000 * 1_000_000_000,
                price=2000 * 100000,
            )
            print(res, "RES")
        except Exception as e:
            print("Exception:", e)

    @pytest.mark.asyncio
    async def test_cancel_order(self, client):
        orders = await client.get_orders_with_trades(status=OrderStatus.OPEN_ORDER)
        order = orders[0]
        await client.cancel_order(order["id"])

    @pytest.mark.asyncio
    async def test_cancel_not_existing_order(self, client):
        try:
            await client.cancel_order(123456789)
        except Exception as e:
            print("Exception:", e)

    @pytest.mark.asyncio
    async def test_get_wallet_operations(self, client):
        startTime = '2023-12-01T00:00:00Z'
        endTime = '2023-12-31T23:59:59Z'
        page = 1
        limit = 10
        txns = await client.get_wallet_transactions(
            startTime=startTime,
            endTime=endTime,
            page=page,
            limit=limit
        )
        print("txns", txns)
        assert isinstance(txns, list)

    @pytest.mark.asyncio
    async def test_get_orders(self, client):
        orders = await client.get_orders(
            page=1,
            limit=10
        )
        print("orders", orders)
        assert isinstance(orders, list)
        assert all(isinstance(order, dict) for order in orders)

    @pytest.mark.asyncio
    async def test_get_pair_list(self, client):
        pairs = await client.get_pair_list()
        print("pairs", pairs)
        assert isinstance(pairs, list)
        assert all(isinstance(pair, dict) for pair in pairs)

    @pytest.mark.asyncio
    async def test_get_pair_info(self, client):
        pair_list = await client.get_pair_list()
        symbol = pair_list[0]['pair_key']
        exchange_info = await client.get_pair_info(symbol)
        print("exchange_info", exchange_info)
        assert isinstance(exchange_info, dict)

    @pytest.mark.asyncio
    async def test_get_price(self, client):
        symbol = TEST_PAIR_NAME
        price_info = await client.get_price(symbol)
        print("price_info", price_info)
        assert isinstance(price_info, dict)

    @pytest.mark.asyncio
    async def test_get_depth(self, client):
        symbol = "moon_usdcs"
        depth = 1000
        depth_info = await client.get_depth(symbol, depth)
        print("moon_usdcs", depth_info)
        assert isinstance(depth_info, dict)

    @pytest.mark.asyncio
    async def test_get_symbols(self, client):
        mask = "algo"
        symbols = await client.get_symbols(mask)
        print("Symbols:", symbols)
        assert isinstance(symbols, list)
        assert all(isinstance(symbol, dict) for symbol in symbols)
        assert all(mask in symbol["pairKey"] for symbol in symbols)

    @pytest.mark.asyncio
    async def test_get_last_trades(self, client):
        symbol = "moon_usdcs"
        last_trades = await client.get_last_trades(symbol)
        print("Last trades for symbol:", symbol, "Trades Data:", last_trades)
        assert isinstance(last_trades, list)

    @pytest.mark.asyncio
    async def test_get_order_by_id(self, client):
        orders = await client.get_orders_with_trades(status=OrderStatus.CANCELLED)
        assert orders, "Orders list is empty, cannot get order ID"
        order_id = orders[0]["id"]
        order_data = await client.get_order_by_id(order_id)
        print("Order:", order_data)
        assert isinstance(order_data, dict)

    @pytest.mark.asyncio
    async def test_withdraw(self, client):
        amount = TEST_WITHDRAW["amount"]
        token_address = TEST_WITHDRAW["tokenAddress"]
        token_chain_id = TEST_WITHDRAW["tokenChainId"]
        recipient = TEST_WITHDRAW["recipient"]

        print(
            f"""\nWithdraw Data:
            Amount: {amount}
            Token Address: {token_address}
            Token Chain ID: {token_chain_id}
            Recipient: {recipient}
            """
        )

        withdraw_data = await client.withdraw(
            amount=amount,
            token_address=token_address,
            token_chain_id=token_chain_id,
            recipient=recipient,
        )
        print("Withdraw Data:", withdraw_data)

    @pytest.mark.asyncio
    async def test_deposit_algorand_algo(self, client):
        walletSigner = Signer.create_signer(TEST_MNEMONIC_KEY)
        result = await client.deposit(walletSigner, 500, 0)
        print("Deposit Data:", result)

    @pytest.mark.asyncio
    async def test_deposit_algorand_asa(self, client):
        walletSigner = Signer.create_signer(TEST_MNEMONIC_KEY)
        result = await client.deposit(walletSigner, 500, 157824770)
        print("Deposit Data:", result)

    @pytest.mark.asyncio
    async def test_deposit_evm(self, client):
        walletSigner = Signer.create_signer(TEST_ETH_PRIVATE_KEY)
        result = await client.deposit(
            walletSigner,
            TEST_WITHDRAW["amount"],
            TEST_WITHDRAW["tokenAddress"],
            "https://sepolia.optimism.io",
        )
        # result = await client.deposit(walletSigner, 500, 1, "https://bsc-pokt.nodies.app")
        print("Deposit Data:", result)

    @pytest.mark.asyncio
    async def test_get_assets(self, client):
        assets = await client.get_assets()
        print("Assets:", assets)
        assert isinstance(assets, list)
        assert all(isinstance(asset, dict) for asset in assets)


@pytest.mark.asyncio
class TestSocket:
    async def test_socket(self, client):
        received_event = asyncio.Event()
        received_data = None
        subscribe_options = {
            "symbol": "",
            "streams": [5],
            "options": {"address": TEST_WALLET_ADDRESS},
        }

        def callback(event, data):
            nonlocal received_data
            print("event", event)
            print("data", data)
            received_data = data
            received_event.set()

        sub_id = await client.subscribe(subscribe_options, callback)
        print("sub_id", sub_id)

        await received_event.wait()
        assert received_data is not None
        assert isinstance(received_data, list)
        assert all(isinstance(data, dict) for data in received_data)
        await client.unsubscribe(sub_id)


@pytest.mark.asyncio
class TestTradingKey:
    async def test_balances(self, trading_client):
        balances = await trading_client.get_balances()
        print("Balances:", balances)
        assert isinstance(balances, list)

    async def test_create_order(self, trading_client):
        pair = await trading_client.get_pair_info(TEST_PAIR_NAME)
        print("Pair:", pair)
        res = await trading_client.create_order(
            pair_id=pair["id"],
            order_side="S",
            order_type="L",
            amount=100000000000000000,
            price=1000,
        )
        print("Order:", res)

    async def test_cancel_order(self, trading_client):
        orders = await trading_client.get_orders_with_trades(
            status=OrderStatus.OPEN_ORDER
        )
        print("\nOrders", orders)
        order = orders[0]
        print("\nOrder", order)
        await trading_client.cancel_order(order["id"])
