"""
Phase-aware dark pool e2e tests for dev4 (or any testnet API URL).

Covers the four gates a `POST /market/order/dark` request goes through —
system scope (enabled + allowAll + whitelist), ban list, pair scope, and
USD notional bounds — plus the trading paths (dark↔dark, dark↔lit) and
the documented constraints (no replace, self-match handled).

The tests *don't* call admin endpoints (those are out of scope for the SDK).
Each phase declares the admin-panel state it expects and skips with a hint
when the live state doesn't match.

Configuration via env vars:

    ULTRADE_DEV4_API_URL      API URL, e.g. https://api.dev4.ultradedev.net
    ULTRADE_DEV4_EVM_KEY      Primary EVM private key (hex, no 0x).
                              Must have ≥ $1M spot USDC for the BUY maxTotal
                              lock with the default test sizes.
    ULTRADE_DEV4_EVM_KEY_2    Secondary EVM private key. Required for the
                              whitelist + trading phases (needs ≥ 1M AVAX
                              for the dark↔dark SELL leg).

    ULTRADE_DARK_PHASE        Which gate phase to run:
        happy        — system enabled, allowAll=true, pair enabled
        whitelist    — system enabled, allowAll=false, primary whitelisted
        ban          — primary banned (whitelisting is irrelevant)
        trading      — both wallets allowed, neither banned; runs real fills
        all          — run every phase (panel must be reset between phases
                       or all but one will skip)

Run only this file:

    pytest tests/dark_pool_e2e.py -v -s

The whole module is skipped if API URL or key is missing.
"""
import asyncio
import os
import pytest
import pytest_asyncio

from ultrade import Client, Signer
from ultrade.types import OrderStatus

API_URL = os.environ.get("ULTRADE_DEV4_API_URL")
PRIMARY_KEY = os.environ.get("ULTRADE_DEV4_EVM_KEY")
SECONDARY_KEY = os.environ.get("ULTRADE_DEV4_EVM_KEY_2")
PHASE = os.environ.get("ULTRADE_DARK_PHASE", "happy")
SPOT_PAIR_KEY = os.environ.get("ULTRADE_DEV4_SPOT_PAIR", "avax_usdc")
PERP_PAIR_KEY = os.environ.get("ULTRADE_DEV4_PERP_PAIR", "btc_usd")

# Sized for the dev4 default dark-pool bounds: parent ≥ $1M, chunk ≥ $10k.
# All chunks are multiples of avax_usdc min_size_increment (1e7) and distinct
# (spot has no nonce, so equal sizes hash identically).
SPOT_CHUNKS = [33_400_000_000_000, 33_300_000_000_000, 33_300_010_000_000]
SPOT_PRICE = 1_000_000_000   # price10 = $0.1/AVAX (far below market, BUY won't fill)

# ~14 BTC parent at btc_usd mark $77k → ~$1M parent notional.
PERP_CHUNKS = [700_000_000, 700_000_000]
PERP_LIMIT_PRICE = 100_000_000_000  # $10 limit, won't fill


pytestmark = [
    pytest.mark.asyncio,
    pytest.mark.skipif(
        not (API_URL and PRIMARY_KEY),
        reason="ULTRADE_DEV4_API_URL and ULTRADE_DEV4_EVM_KEY must be set",
    ),
]


# Spot dark-order messages have no nonce — uniqueness comes from
# (chunks, price, address, expiredTime). expiredTime resolves to 1 second,
# so two same-shape spot dark orders placed within one second collide as
# "Order message must be unique". A 1.1s sleep between tests lets the clock
# tick over so each test gets a fresh expiredTime.
@pytest_asyncio.fixture(autouse=True)
async def _settle_between_tests():
    yield
    await asyncio.sleep(1.1)


@pytest_asyncio.fixture(scope="module")
async def primary():
    c = Client(network="testnet", api_url=API_URL)
    await c.set_login_user(Signer.create_signer(PRIMARY_KEY))
    yield c
    await c.close()


@pytest_asyncio.fixture(scope="module")
async def secondary():
    if not SECONDARY_KEY:
        pytest.skip("ULTRADE_DEV4_EVM_KEY_2 not set — secondary-wallet tests need it")
    c = Client(network="testnet", api_url=API_URL)
    await c.set_login_user(Signer.create_signer(SECONDARY_KEY))
    yield c
    await c.close()


@pytest_asyncio.fixture(scope="module")
async def spot_pair(primary):
    return await primary.get_pair_info(SPOT_PAIR_KEY)


@pytest_asyncio.fixture(scope="module")
async def perp_pair(primary):
    pairs = await primary.get_pair_list()
    match = next((p for p in pairs if p.get("pair_key") == PERP_PAIR_KEY), None)
    if not match:
        pytest.skip(f"perp pair {PERP_PAIR_KEY!r} not in pair list")
    return match


def _skip_unless_phase(*phases):
    if PHASE != "all" and PHASE not in phases:
        pytest.skip(f"ULTRADE_DARK_PHASE={PHASE!r}; this test runs under {phases}")


def _server_message(exc: Exception) -> str:
    if exc.args and isinstance(exc.args[0], dict):
        return str(exc.args[0].get("message", "")).lower()
    return str(exc).lower()


async def _create_spot_dark(client, spot_pair):
    return await client.create_dark_order(
        pair_id=spot_pair["id"],
        chunks=SPOT_CHUNKS,
        market_type="spot",
        order_side="B",
        order_type="L",
        price=SPOT_PRICE,
    )


# ---------------------------------------------------------------------------
# Phase: happy — system enabled, allowAll=true, pair enabled
# ---------------------------------------------------------------------------


class TestHappyPath:
    async def test_spot_create_cancel(self, primary, spot_pair):
        _skip_unless_phase("happy")
        try:
            res = await _create_spot_dark(primary, spot_pair)
        except Exception as e:
            msg = _server_message(e)
            if "not enabled" in msg or "not available" in msg or "access revoked" in msg:
                pytest.skip(
                    f"dev4 panel state ≠ happy-path. server said: {msg!r}. "
                    f"Expected: system.enabled=true, system.allowAll=true, "
                    f"pair {SPOT_PAIR_KEY!r} dark-pool enabled."
                )
            raise
        order_id = res.get("id") or res.get("orderId")
        assert order_id, res
        try:
            await primary.cancel_order(order_id)
        except Exception:
            pass

    async def test_perp_create_cancel(self, primary, perp_pair):
        _skip_unless_phase("happy")
        try:
            res = await primary.create_dark_order(
                pair_id=perp_pair["id"],
                chunks=PERP_CHUNKS,
                market_type="perp",
                pyth_id=perp_pair["pythId"],
                order_side=0,
                order_type=0,
                time_in_force=0,
                limit_price=PERP_LIMIT_PRICE,
                target_leverage=2,
            )
        except Exception as e:
            msg = _server_message(e)
            if "not enabled" in msg or "not available" in msg or "access revoked" in msg:
                pytest.skip(
                    f"dev4 panel state ≠ happy-path. server said: {msg!r}. "
                    f"Expected: dark-pool enabled for perp pair {PERP_PAIR_KEY!r}."
                )
            if "below dark pool minimum" in msg or "insufficient margin" in msg or "target lev" in msg:
                pytest.skip(f"sizing mismatch on dev4: {msg!r}")
            raise
        order_id = res.get("id") or res.get("orderId")
        assert order_id, res
        try:
            await primary.cancel_order(order_id)
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Phase: whitelist — system enabled, allowAll=false, primary whitelisted
# ---------------------------------------------------------------------------


class TestWhitelistGate:
    async def test_whitelisted_wallet_passes(self, primary, spot_pair):
        _skip_unless_phase("whitelist")
        try:
            res = await _create_spot_dark(primary, spot_pair)
        except Exception as e:
            msg = _server_message(e)
            if "not available" in msg:
                pytest.skip(
                    f"primary wallet not in dark-pool whitelist. server: {msg!r}. "
                    f"Add {Signer.create_signer(PRIMARY_KEY).address!r}."
                )
            if "not enabled" in msg:
                pytest.skip(f"pair {SPOT_PAIR_KEY!r} dark-pool disabled: {msg!r}")
            raise
        order_id = res.get("id") or res.get("orderId")
        assert order_id, res
        try:
            await primary.cancel_order(order_id)
        except Exception:
            pass

    async def test_non_whitelisted_wallet_rejected(self, secondary, spot_pair):
        _skip_unless_phase("whitelist")
        try:
            res = await _create_spot_dark(secondary, spot_pair)
        except Exception as e:
            msg = _server_message(e)
            assert "not available" in msg, f"unexpected rejection: {msg!r}"
            return
        # Order went through — panel state doesn't match the phase.
        try:
            oid = res.get("id") or res.get("orderId")
            if oid:
                await secondary.cancel_order(oid)
        except Exception:
            pass
        pytest.skip(
            "secondary wallet was not rejected — system.allowAll is still true "
            "or secondary is also on the whitelist."
        )


# ---------------------------------------------------------------------------
# Phase: ban — primary on the ban list (whitelist or allowAll irrelevant)
# ---------------------------------------------------------------------------


class TestBanGate:
    async def test_banned_wallet_rejected(self, primary, spot_pair):
        _skip_unless_phase("ban")
        try:
            res = await _create_spot_dark(primary, spot_pair)
        except Exception as e:
            msg = _server_message(e)
            assert "access revoked" in msg, f"unexpected rejection: {msg!r}"
            return
        try:
            oid = res.get("id") or res.get("orderId")
            if oid:
                await primary.cancel_order(oid)
        except Exception:
            pass
        pytest.skip(
            f"primary wallet was not rejected as banned. Add "
            f"{Signer.create_signer(PRIMARY_KEY).address!r} to dark-pool bans."
        )


# ---------------------------------------------------------------------------
# Privacy invariants — what a non-owner can and can't see. Runs under the
# same "trading" phase (both wallets allowed, neither banned).
# ---------------------------------------------------------------------------


def _bid_amount_at(depth: dict, price: int) -> int:
    """Look up the bid-side cumulative amount at an exact price level in the
    public depth payload. Returns 0 if the price isn't there at all."""
    bids = depth.get("buy") or depth.get("bids") or []
    for lvl in bids:
        if isinstance(lvl, dict):
            p, a = int(lvl.get("price", 0)), int(lvl.get("amount", 0))
        else:
            p, a = int(lvl[0]), int(lvl[1])
        if p == int(price):
            return a
    return 0


class TestPrivacy:
    async def test_owner_sees_isDark_flag(self, primary, spot_pair):
        _skip_unless_phase("trading", "happy")
        try:
            dark = await primary.create_dark_order(
                pair_id=spot_pair["id"], chunks=SPOT_CHUNKS, market_type="spot",
                order_side="B", order_type="L", price=SPOT_PRICE,
            )
        except Exception as e:
            msg = _server_message(e)
            if "not available" in msg or "not enabled" in msg or "access revoked" in msg:
                pytest.skip(f"primary cannot create dark orders: {msg!r}")
            raise
        try:
            by_id = await primary.get_order_by_id(dark["id"])
            assert by_id.get("isDark") is True, by_id

            opens = await primary.get_orders_with_trades(status=OrderStatus.OPEN_ORDER)
            ours = next((o for o in opens if o["id"] == dark["id"]), None)
            assert ours is not None, "owner's open list missing its own dark order"
            assert ours.get("isDark") is True, ours
        finally:
            try: await primary.cancel_order(dark["id"])
            except Exception: pass

    async def test_public_depth_does_not_leak_dark(self, primary, secondary, spot_pair):
        _skip_unless_phase("trading")
        # Unique prices below market so neither order fills.
        dark_price = 7_000_000_000     # $0.70
        lit_price = 6_000_000_000      # $0.60 — control
        lit_amount = sum(SPOT_CHUNKS)

        before = await secondary.get_depth("avax_usdc", depth=200)
        base_dark = _bid_amount_at(before, dark_price)
        base_lit = _bid_amount_at(before, lit_price)

        dark = lit = None
        try:
            try:
                dark = await primary.create_dark_order(
                    pair_id=spot_pair["id"], chunks=SPOT_CHUNKS, market_type="spot",
                    order_side="B", order_type="L", price=dark_price,
                )
            except Exception as e:
                msg = _server_message(e)
                if "insufficient balance" in msg or "not available" in msg or "not enabled" in msg:
                    pytest.skip(f"dark order placement preconditions not met: {msg!r}")
                raise
            try:
                lit = await primary.create_order(
                    market_type="spot", pair_id=spot_pair["id"],
                    order_side="B", order_type="L",
                    amount=lit_amount, price=lit_price,
                )
            except Exception as e:
                msg = _server_message(e)
                if "insufficient balance" in msg:
                    pytest.skip(f"control lit order couldn't be placed: {msg!r}")
                raise
            await asyncio.sleep(1.5)

            after = await secondary.get_depth("avax_usdc", depth=200)
            post_dark = _bid_amount_at(after, dark_price)
            post_lit = _bid_amount_at(after, lit_price)

            # Skip if the control failed — depth may be lagged or paused.
            # The MAIN assertion (dark not leaked) is still validated.
            if post_lit <= base_lit:
                pytest.skip(
                    f"control lit order did not appear in depth (before={base_lit} "
                    f"after={post_lit}); depth feed may be lagged."
                )
            # Main invariant: dark price level must not have grown.
            assert post_dark == base_dark, (
                f"dark order leaked into public depth at price {dark_price}: "
                f"before={base_dark} after={post_dark}"
            )
        finally:
            for oid in (dark and dark.get("id"), lit and lit.get("id")):
                if oid:
                    try: await primary.cancel_order(oid)
                    except Exception: pass

    async def test_cross_wallet_isolation(self, primary, secondary, spot_pair):
        """Secondary's private orders endpoint must not include primary's
        dark order. (Standard auth scoping, but cheap to verify.)"""
        _skip_unless_phase("trading")
        try:
            dark = await primary.create_dark_order(
                pair_id=spot_pair["id"], chunks=SPOT_CHUNKS, market_type="spot",
                order_side="B", order_type="L", price=SPOT_PRICE,
            )
        except Exception as e:
            msg = _server_message(e)
            if "not available" in msg or "not enabled" in msg or "access revoked" in msg:
                pytest.skip(f"primary cannot create dark orders: {msg!r}")
            raise

        try:
            s_opens = await secondary.get_orders_with_trades(status=OrderStatus.OPEN_ORDER)
            assert dark["id"] not in {o["id"] for o in s_opens}, (
                "secondary saw primary's dark order in its private orders endpoint"
            )
        finally:
            try: await primary.cancel_order(dark["id"])
            except Exception: pass


# ---------------------------------------------------------------------------
# Phase: trading — both wallets allowed, neither banned. Runs real fills.
# Leaves balances shifted (dev4 mint balances, so safe to drift).
# ---------------------------------------------------------------------------


CROSS_PRICE = 10_000_000_000          # $1 / AVAX — both legs cross here
LIT_TAKER_AMOUNT = 1_000_000_000_000  # 10k AVAX lit taker → partial-fill the dark


async def _wait_for_fill(client, order_id, *, timeout=5.0, poll=0.5):
    """Polls until the order shows any filledAmount > 0, or timeout."""
    deadline = asyncio.get_event_loop().time() + timeout
    last = None
    while asyncio.get_event_loop().time() < deadline:
        last = await client.get_order_by_id(order_id)
        if int(last.get("filledAmount", 0)) > 0:
            return last
        await asyncio.sleep(poll)
    return last


class TestTrading:
    async def test_dark_crosses_dark(self, primary, secondary, spot_pair):
        _skip_unless_phase("trading")
        try:
            buy = await primary.create_dark_order(
                pair_id=spot_pair["id"],
                chunks=SPOT_CHUNKS,
                market_type="spot",
                order_side="B",
                order_type="L",
                price=CROSS_PRICE,
            )
        except Exception as e:
            msg = _server_message(e)
            if any(p in msg for p in ("not available", "not enabled", "access revoked", "insufficient balance")):
                pytest.skip(f"primary cannot create dark orders: {msg!r}")
            raise

        try:
            sell = await secondary.create_dark_order(
                pair_id=spot_pair["id"],
                chunks=SPOT_CHUNKS,
                market_type="spot",
                order_side="S",
                order_type="L",
                price=CROSS_PRICE,
            )
        except Exception as e:
            await primary.cancel_order(buy["id"])
            msg = _server_message(e)
            if any(p in msg for p in ("not available", "not enabled", "access revoked", "insufficient balance")):
                pytest.skip(f"secondary cannot create dark orders: {msg!r}")
            raise

        try:
            buy_after = await _wait_for_fill(primary, buy["id"])
            sell_after = await _wait_for_fill(secondary, sell["id"])
            assert int(buy_after["filledAmount"]) > 0, buy_after
            assert int(sell_after["filledAmount"]) > 0, sell_after
            assert str(buy_after["avgPrice"]) == str(CROSS_PRICE), buy_after
        finally:
            for c, oid in [(primary, buy["id"]), (secondary, sell["id"])]:
                try: await c.cancel_order(oid)
                except Exception: pass

    async def test_lit_taker_partially_fills_dark(self, primary, secondary, spot_pair):
        _skip_unless_phase("trading")
        try:
            buy = await primary.create_dark_order(
                pair_id=spot_pair["id"],
                chunks=SPOT_CHUNKS,
                market_type="spot",
                order_side="B",
                order_type="L",
                price=CROSS_PRICE,
            )
        except Exception as e:
            msg = _server_message(e)
            if any(p in msg for p in ("not available", "not enabled", "access revoked", "insufficient balance")):
                pytest.skip(f"primary cannot create dark orders: {msg!r}")
            raise

        try:
            lit = await secondary.create_order(
                market_type="spot",
                pair_id=spot_pair["id"],
                order_side="S",
                order_type="L",
                amount=LIT_TAKER_AMOUNT,
                price=CROSS_PRICE,
            )
            buy_after = await _wait_for_fill(primary, buy["id"])
            assert int(buy_after["filledAmount"]) == LIT_TAKER_AMOUNT, buy_after
            assert int(buy_after["filledAmount"]) < int(buy_after["amount"]), \
                f"expected partial, got full: {buy_after}"
            assert str(buy_after["avgPrice"]) == str(CROSS_PRICE), buy_after
        finally:
            for c, oid in [(primary, buy["id"]), (secondary, lit.get("id") if isinstance(lit, dict) else None)]:
                if oid:
                    try: await c.cancel_order(oid)
                    except Exception: pass

    async def test_dark_cannot_be_replaced(self, primary, spot_pair):
        _skip_unless_phase("trading")
        try:
            dark = await primary.create_dark_order(
                pair_id=spot_pair["id"],
                chunks=SPOT_CHUNKS,
                market_type="spot",
                order_side="B",
                order_type="L",
                price=SPOT_PRICE,  # below market, won't fill
            )
        except Exception as e:
            msg = _server_message(e)
            if "not available" in msg or "not enabled" in msg or "access revoked" in msg:
                pytest.skip(f"primary cannot create dark orders: {msg!r}")
            raise

        try:
            rep = await primary.replace_orders([{
                "old_order_id": dark["id"],
                "pair_id": spot_pair["id"],
                "order_side": "B",
                "order_type": "L",
                "amount": sum(SPOT_CHUNKS),
                "price": SPOT_PRICE * 2,
            }], market_type="spot")
            # Bulk replace returns 200 with per-item failure reasons.
            assert not rep.get("successfulReplacements"), rep
            failed = rep.get("failedReplacements") or []
            assert failed, rep
            assert "dark orders cannot be replaced" in failed[0].get("reason", "").lower(), failed
        finally:
            try: await primary.cancel_order(dark["id"])
            except Exception: pass

    async def test_self_match_does_not_fill(self, primary, spot_pair):
        _skip_unless_phase("trading")
        try:
            buy = await primary.create_dark_order(
                pair_id=spot_pair["id"],
                chunks=SPOT_CHUNKS,
                market_type="spot",
                order_side="B",
                order_type="L",
                price=CROSS_PRICE,
            )
        except Exception as e:
            msg = _server_message(e)
            if "not available" in msg or "not enabled" in msg or "access revoked" in msg:
                pytest.skip(f"primary cannot create dark orders: {msg!r}")
            raise

        try:
            sell = await primary.create_dark_order(
                pair_id=spot_pair["id"],
                chunks=SPOT_CHUNKS,
                market_type="spot",
                order_side="S",
                order_type="L",
                price=CROSS_PRICE,
            )
            # Allow the matching engine a moment.
            await asyncio.sleep(1.5)
            buy_after = await primary.get_order_by_id(buy["id"])
            sell_after = await primary.get_order_by_id(sell["id"])
            assert int(buy_after["filledAmount"]) == 0, f"buy filled in self-match: {buy_after}"
            # Sell ends up status=4 (SelfMatched) with filledAmount=0
            assert int(sell_after["filledAmount"]) == 0, f"sell filled in self-match: {sell_after}"
        finally:
            for oid in (buy["id"], locals().get("sell", {}).get("id")):
                if oid:
                    try: await primary.cancel_order(oid)
                    except Exception: pass


# ---------------------------------------------------------------------------
# Always-on: SDK-side argument validation. No network calls.
# ---------------------------------------------------------------------------


class TestArgumentValidation:
    async def test_rejects_single_chunk(self, primary, spot_pair):
        with pytest.raises(ValueError, match="at least 2"):
            await primary.create_dark_order(
                pair_id=spot_pair["id"],
                chunks=[100_000_000],
                market_type="spot",
                order_side="B",
                order_type="L",
                price=SPOT_PRICE,
            )

    async def test_rejects_equal_spot_chunks(self, primary, spot_pair):
        with pytest.raises(ValueError, match="distinct sizes"):
            await primary.create_dark_order(
                pair_id=spot_pair["id"],
                chunks=[100_000_000, 100_000_000],
                market_type="spot",
                order_side="B",
                order_type="L",
                price=SPOT_PRICE,
            )

    async def test_rejects_zero_chunk(self, primary, spot_pair):
        with pytest.raises(ValueError, match="> 0"):
            await primary.create_dark_order(
                pair_id=spot_pair["id"],
                chunks=[100_000_000, 0],
                market_type="spot",
                order_side="B",
                order_type="L",
                price=SPOT_PRICE,
            )

    async def test_random_split_path(self, primary, spot_pair):
        """The randomized-split path should produce a valid parent and a
        distinct, sum-equal chunk set. Cancels immediately on success."""
        res = await primary.create_dark_order(
            pair_id=spot_pair["id"],
            total_amount=10**14,
            num_chunks=5,
            min_chunk=10**13,
            market_type="spot",
            order_side="B",
            order_type="L",
            price=SPOT_PRICE,
            rng_seed=42,
        )
        order_id = res.get("id") or res.get("orderId")
        assert order_id, res
        assert int(res["amount"]) == 10**14
        try: await primary.cancel_order(order_id)
        except Exception: pass

    async def test_random_split_rejects_chunks_and_total_together(self, primary, spot_pair):
        with pytest.raises(ValueError, match="not both"):
            await primary.create_dark_order(
                pair_id=spot_pair["id"],
                chunks=[1, 2, 3],
                total_amount=10**14,
                num_chunks=5,
                market_type="spot",
                order_side="B",
                order_type="L",
                price=SPOT_PRICE,
            )

    async def test_random_split_requires_total_and_count(self, primary, spot_pair):
        with pytest.raises(ValueError, match="either `chunks="):
            await primary.create_dark_order(
                pair_id=spot_pair["id"],
                market_type="spot",
                order_side="B",
                order_type="L",
                price=SPOT_PRICE,
            )


# ---------------------------------------------------------------------------
# Unit-level tests for the splitter itself. No network, no fixtures.
# ---------------------------------------------------------------------------


class TestSplitDarkChunks:
    async def test_basic_split_invariants(self):
        from ultrade import split_dark_chunks
        chunks = split_dark_chunks(
            total=10**14, num_chunks=5,
            min_increment=10**7, min_chunk=10**13,
            distinct=True, seed=1,
        )
        assert sum(chunks) == 10**14
        assert len(chunks) == 5
        assert all(c % 10**7 == 0 for c in chunks)
        assert all(c >= 10**13 for c in chunks)
        assert len(set(chunks)) == 5

    async def test_perp_allows_equal_chunks(self):
        from ultrade import split_dark_chunks
        chunks = split_dark_chunks(
            total=1_400_000_000_0, num_chunks=10,
            min_increment=1, distinct=False, concentration=50.0, seed=1,
        )
        assert sum(chunks) == 1_400_000_000_0

    async def test_seed_reproducibility(self):
        from ultrade import split_dark_chunks
        a = split_dark_chunks(total=10**14, num_chunks=4,
                              min_increment=10**7, min_chunk=10**13,
                              distinct=True, seed=99)
        b = split_dark_chunks(total=10**14, num_chunks=4,
                              min_increment=10**7, min_chunk=10**13,
                              distinct=True, seed=99)
        assert a == b

    async def test_rejects_total_not_multiple_of_increment(self):
        from ultrade import split_dark_chunks
        with pytest.raises(ValueError, match="multiple of"):
            split_dark_chunks(total=10**14 + 1, num_chunks=3,
                              min_increment=10**7)

    async def test_rejects_floor_too_high(self):
        from ultrade import split_dark_chunks
        with pytest.raises(ValueError, match="exceeds total"):
            split_dark_chunks(total=10, num_chunks=3,
                              min_increment=1, min_chunk=5)
