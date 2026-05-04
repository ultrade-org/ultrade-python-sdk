"""
Integration tests against the dev4 environment (or any testnet API URL).

Configuration via env vars:

    ULTRADE_DEV4_API_URL    API URL, e.g. https://api.dev4.ultradedev.net
    ULTRADE_DEV4_EVM_KEY    EVM private key (hex, no 0x). Account needs USDC
                            in spot + AVAX so the configured pair can trade.
    ULTRADE_DEV4_SPOT_PAIR  Spot pair_key (default: avax_usdc)
    ULTRADE_DEV4_PERP_PAIR  Perp pair_key (default: btc_usd)

Run only this file:

    pytest tests/dev4_test.py -v -s

The whole module is skipped if API URL or key is missing, so dev4 isn't a
blocker for the rest of the suite.

Notes:
- Tests use limit prices far from market and are self-cancelling so they
  don't leave open orders behind.
- `test_deposit_margin_asset` tolerates "fee too small" — that's a server-side
  Redis budget knob (`*:extraTxns`), not an SDK bug. Bump it via redis-cli on
  dev4 if you want this test to pass: `redis-cli set depositCa:extraTxns 20`.
"""
import os
import asyncio
import pytest
import pytest_asyncio

from ultrade import Client, Signer
from ultrade.types import OrderStatus

API_URL = os.environ.get("ULTRADE_DEV4_API_URL")
EVM_KEY = os.environ.get("ULTRADE_DEV4_EVM_KEY")
SPOT_PAIR_KEY = os.environ.get("ULTRADE_DEV4_SPOT_PAIR", "avax_usdc")
PERP_PAIR_KEY = os.environ.get("ULTRADE_DEV4_PERP_PAIR", "btc_usd")

USDC_TOKEN_INDEX = "0x4343545055534443000000000000000000000000000000000000000000000000"
USDC_CHAIN = 65537

pytestmark = [
    pytest.mark.asyncio,
    pytest.mark.skipif(
        not (API_URL and EVM_KEY),
        reason="ULTRADE_DEV4_API_URL and ULTRADE_DEV4_EVM_KEY must be set",
    ),
]


@pytest_asyncio.fixture(scope="module")
async def dev4_client():
    client = Client(network="testnet", api_url=API_URL)
    await client.set_login_user(Signer.create_signer(EVM_KEY))
    yield client
    await client.close()


@pytest_asyncio.fixture(scope="module")
async def spot_pair(dev4_client):
    return await dev4_client.get_pair_info(SPOT_PAIR_KEY)


@pytest_asyncio.fixture(scope="module")
async def perp_pair(dev4_client):
    # `get_pair_info` doesn't include `pythId` for perps; the pair list does.
    pairs = await dev4_client.get_pair_list()
    match = next((p for p in pairs if p.get("pair_key") == PERP_PAIR_KEY), None)
    if not match:
        pytest.skip(f"perp pair {PERP_PAIR_KEY!r} not in pair list")
    return match


def _is_fee_too_small(exc: Exception) -> bool:
    return "fee too small" in str(exc).lower()


def _is_dev4_assert(exc: Exception) -> bool:
    """Detects dev4 contract assert errors (logic eval pc=NN). These are
    server-side state issues — not the SDK — so the test should skip rather
    than fail."""
    s = str(exc).lower()
    return "logic eval error" in s or "assert failed" in s


# ---------------------------------------------------------------------------
# Read-only endpoints
# ---------------------------------------------------------------------------


class TestReads:
    async def test_ping(self, dev4_client):
        latency = await dev4_client.ping()
        assert isinstance(latency, int)

    async def test_get_pair_info_spot(self, dev4_client):
        pair = await dev4_client.get_pair_info(SPOT_PAIR_KEY)
        assert pair["pair_key"] == SPOT_PAIR_KEY

    async def test_get_pair_info_perp(self, dev4_client):
        pair = await dev4_client.get_pair_info(PERP_PAIR_KEY)
        assert pair["pair_key"] == PERP_PAIR_KEY

    async def test_get_pair_list(self, dev4_client):
        pairs = await dev4_client.get_pair_list()
        assert isinstance(pairs, list) and pairs

    async def test_get_balances(self, dev4_client):
        balances = await dev4_client.get_balances()
        assert isinstance(balances, list)

    async def test_get_equity(self, dev4_client):
        equity = await dev4_client.get_equity()
        assert "accountAddress" in equity

    async def test_get_positions(self, dev4_client):
        assert isinstance(await dev4_client.get_positions(), list)

    async def test_get_margin_assets(self, dev4_client):
        assert isinstance(await dev4_client.get_margin_assets(), list)

    async def test_get_market_margin_assets(self, dev4_client):
        assets = await dev4_client.get_market_margin_assets()
        assert isinstance(assets, list) and assets

    async def test_get_orders(self, dev4_client):
        assert isinstance(await dev4_client.get_orders(), list)

    async def test_get_orders_with_trades(self, dev4_client):
        orders = await dev4_client.get_orders_with_trades(status=OrderStatus.OPEN_ORDER)
        assert isinstance(orders, list)

    async def test_get_wallet_transactions(self, dev4_client):
        txs = await dev4_client.get_wallet_transactions(limit=5)
        assert isinstance(txs, list)


# ---------------------------------------------------------------------------
# Spot lifecycle: create / replace / cancel
# ---------------------------------------------------------------------------


def _spot_kwargs(pair_id: int) -> dict:
    """Buy 1 base unit at 1 quote unit — far below market so it doesn't fill."""
    return dict(
        market_type="spot",
        pair_id=pair_id,
        order_side="B",
        order_type="L",
        amount=100_000_000,    # size8: 1 base unit
        price=10_000_000_000,  # price10: 1 quote per base
    )


class TestSpotLifecycle:
    async def test_create_replace_cancel(self, dev4_client, spot_pair):
        kw = _spot_kwargs(spot_pair["id"])
        created = await dev4_client.create_order(**kw)
        order_id = created["id"]
        assert created["status"] == 1, created

        try:
            replacement = {**{k: v for k, v in kw.items() if k != "market_type"},
                           "old_order_id": order_id,
                           "price": 20_000_000_000}
            rep = await dev4_client.replace_orders([replacement], market_type="spot")
            assert rep["successfulReplacements"], rep
            new_id = rep["successfulReplacements"][0]["newOrderId"]
            assert new_id != order_id
            order_id = new_id
        finally:
            await dev4_client.cancel_order(order_id)

    async def test_bulk_spot(self, dev4_client, spot_pair):
        # Bulks with identical signed messages are rejected as duplicates by
        # the server, so vary one field per order.
        kw = _spot_kwargs(spot_pair["id"])
        kw.pop("market_type")
        specs = [{**kw, "price": kw["price"] + i * 2_000_000_000} for i in range(2)]
        result = await dev4_client.create_bulk_orders(specs, market_type="spot")
        ids = [s["orderId"] for s in result.get("successfulOrders", [])]
        try:
            assert ids, result
        finally:
            if ids:
                await dev4_client.cancel_bulk_orders(ids, pair_id=spot_pair["id"])


# ---------------------------------------------------------------------------
# Perp lifecycle: create / replace / cancel. Skip if no perp margin.
# ---------------------------------------------------------------------------


def _perp_kwargs(pair_id: int, pyth_id: str) -> dict:
    """Long limit far below mark so it doesn't fill."""
    return dict(
        market_type="perp",
        pair_id=pair_id,
        pyth_id=pyth_id,
        order_side=0,             # LONG
        order_type=0,             # LIMIT
        time_in_force=0,          # GTC
        size_lots=20_000,         # at min order size for btc_usd on dev4
        limit_price=700_000_000_000,
        target_leverage=2,
    )


async def _has_perp_margin(client) -> bool:
    eq = await client.get_equity()
    perp_total = (eq.get("perp", {}) or {}).get("balance", {}).get("total")
    try:
        return float(perp_total or 0) > 0
    except (TypeError, ValueError):
        return False


class TestPerpLifecycle:
    async def test_create_cancel(self, dev4_client, perp_pair):
        if not await _has_perp_margin(dev4_client):
            pytest.skip("Account has no perp margin; deposit USDC to perps first")
        kw = _perp_kwargs(perp_pair["id"], perp_pair["pythId"])
        created = await dev4_client.create_order(**kw)
        order_id = created.get("id") or created.get("orderId")
        assert order_id, created
        await dev4_client.cancel_order(order_id)

    async def test_bulk_perp(self, dev4_client, perp_pair):
        if not await _has_perp_margin(dev4_client):
            pytest.skip("Account has no perp margin; deposit USDC to perps first")
        kw = _perp_kwargs(perp_pair["id"], perp_pair["pythId"])
        spec = {k: v for k, v in kw.items() if k != "market_type"}
        result = await dev4_client.create_bulk_orders([spec], market_type="perp")
        ids = [s["orderId"] for s in result.get("successfulOrders", [])]
        try:
            assert ids, result
        finally:
            for oid in ids:
                try:
                    await dev4_client.cancel_order(oid)
                except Exception:
                    pass


# ---------------------------------------------------------------------------
# Margin asset deposit. Tolerates the dev4 "fee too small" Redis-budget issue.
# ---------------------------------------------------------------------------


class TestMarginAsset:
    async def test_deposit_one_usdc(self, dev4_client):
        balances = await dev4_client.get_balances()
        usdc = next(
            (b for b in balances if b.get("tokenAddress") == USDC_TOKEN_INDEX
             and b.get("tokenChainId") == USDC_CHAIN),
            None,
        )
        if not usdc or int(usdc["amount"]) - int(usdc.get("marginAmount", 0)) < 1_000_000:
            pytest.skip("Account spot USDC balance < 1 USDC; cannot deposit")

        try:
            res = await dev4_client.deposit_margin_asset(
                token_amount=1_000_000,
                token_index=USDC_TOKEN_INDEX,
                token_chain_id=USDC_CHAIN,
            )
        except Exception as e:
            if _is_fee_too_small(e):
                pytest.skip(
                    "Server inner-txn fee too small. Bump 'depositCa:extraTxns' "
                    "in dev4 redis (e.g. `redis-cli set depositCa:extraTxns 20`)."
                )
            if _is_dev4_assert(e):
                pytest.skip(f"dev4 contract assert (server-side state): {e}")
            raise
        assert res.get("txId"), res

    async def test_mark_to_now(self, dev4_client):
        # Returns 200 even with no positions — just shouldn't throw.
        await dev4_client.mark_margin_assets_to_now()

    async def test_usd_value(self, dev4_client):
        await dev4_client.get_margin_assets_usd_value()


# ---------------------------------------------------------------------------
# Negative paths
# ---------------------------------------------------------------------------


class TestNegativePaths:
    async def test_cancel_nonexistent_order(self, dev4_client):
        with pytest.raises(Exception) as exc_info:
            await dev4_client.cancel_order(999_999_999_999)
        assert "not found" in str(exc_info.value).lower()

    async def test_cancel_bulk_nonexistent(self, dev4_client, spot_pair):
        result = await dev4_client.cancel_bulk_orders(
            [999_999_999_999], pair_id=spot_pair["id"]
        )
        assert result["failedOrders"], result
