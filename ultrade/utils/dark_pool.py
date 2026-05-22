"""
Random splitter for dark-order chunks. Produces an obfuscated split that
avoids the round-number / arithmetic-pattern leak you get with manually
chosen chunk sizes (e.g. `[100k, 100k, 100k]` or `[40k, 30k, 30k]`).

Algorithm: pre-allocate the per-chunk floor, distribute the remainder via
Dirichlet weights, quantize to the increment, then break ties so spot chunks
end up distinct (the spot order message has no nonce — equal sizes would
hash identically and be rejected as duplicates).

The split is shuffled before returning so the chunk *order* doesn't carry
information either.
"""
import random as _r
from typing import Optional


def split_dark_chunks(
    total: int,
    num_chunks: int,
    *,
    min_increment: int = 1,
    min_chunk: Optional[int] = None,
    distinct: bool = True,
    concentration: float = 2.0,
    seed: Optional[int] = None,
) -> list[int]:
    """
    Randomly split `total` into `num_chunks` integer chunks.

    Args:
        total: Sum the chunks must equal. Must be a multiple of `min_increment`.
        num_chunks: Number of chunks; must be ≥ 2.
        min_increment: Each chunk is a multiple of this. For spot this is the
            pair's `min_size_increment` (server-validated). For perp pass 1.
        min_chunk: Optional minimum size per chunk (after quantizing up to the
            nearest `min_increment`). Use this when the server enforces a
            per-chunk USD floor and you can convert that floor to size units.
            Defaults to `min_increment`.
        distinct: If True (default for spot), the returned chunks are pairwise
            distinct. Set to False for perp where the random nonce makes equal
            sizes safe.
        concentration: Dirichlet alpha. ~1 = high variance (one chunk may
            dominate), ~5+ = chunks cluster near equal sizes. Default 2.0
            produces visible variance without extreme outliers.
        seed: If set, the split is reproducible. Use only in tests.

    Returns:
        list[int]: chunks summing to `total`, each a multiple of
        `min_increment`, each ≥ floor, distinct iff requested.

    Raises:
        ValueError: when the inputs are inconsistent (total not divisible by
        increment, too small for the requested chunk count, etc.).
    """
    if num_chunks < 2:
        raise ValueError("split_dark_chunks: num_chunks must be >= 2")
    if total <= 0:
        raise ValueError("split_dark_chunks: total must be positive")
    if min_increment <= 0:
        raise ValueError("split_dark_chunks: min_increment must be positive")
    if total % min_increment != 0:
        raise ValueError(
            f"split_dark_chunks: total ({total}) must be a multiple of "
            f"min_increment ({min_increment})"
        )

    # Round min_chunk UP to the next min_increment (a chunk smaller than
    # min_chunk is unacceptable, so we never round down).
    floor = min_increment
    if min_chunk is not None and min_chunk > 0:
        floor = ((int(min_chunk) + min_increment - 1) // min_increment) * min_increment
    if floor * num_chunks > total:
        raise ValueError(
            f"split_dark_chunks: floor*num_chunks ({floor}*{num_chunks}) "
            f"exceeds total ({total})"
        )

    rng = _r.Random(seed) if seed is not None else _r.SystemRandom()

    # Pre-allocate floors; distribute the rest.
    pool_units = (total - floor * num_chunks) // min_increment

    # Dirichlet weights via the gamma-normalize trick (no numpy dep).
    weights = [rng.gammavariate(concentration, 1.0) for _ in range(num_chunks)]
    total_w = sum(weights) or 1.0
    weights = [w / total_w for w in weights]

    raw = [w * pool_units for w in weights]
    int_alloc = [int(x) for x in raw]
    leftover = pool_units - sum(int_alloc)
    # Distribute rounding leftover to chunks with the largest fractional parts.
    frac_order = sorted(range(num_chunks), key=lambda i: raw[i] - int_alloc[i], reverse=True)
    for k in range(leftover):
        int_alloc[frac_order[k % num_chunks]] += 1

    chunks = [floor + a * min_increment for a in int_alloc]

    if distinct:
        chunks = _make_distinct(chunks, min_increment=min_increment, floor=floor, rng=rng)

    rng.shuffle(chunks)

    # Invariants — cheap to check, expensive if wrong on production traffic.
    if sum(chunks) != total:
        raise ValueError(f"split_dark_chunks: internal error, sum {sum(chunks)} != {total}")
    if any(c % min_increment != 0 for c in chunks):
        raise ValueError("split_dark_chunks: internal error, non-increment chunk produced")
    if any(c < floor for c in chunks):
        raise ValueError("split_dark_chunks: internal error, chunk below floor")
    if distinct and len(set(chunks)) != num_chunks:
        raise ValueError(
            "split_dark_chunks: could not produce distinct chunks — total "
            "too tight given num_chunks and floor"
        )
    return chunks


def _make_distinct(chunks: list[int], *, min_increment: int, floor: int, rng) -> list[int]:
    """Resolve duplicates by moving one increment from a chunk with headroom
    above the floor to its colliding sibling. Preserves sum and floor."""
    max_passes = 4 * len(chunks)
    for _ in range(max_passes):
        seen = {}
        collision = None
        for i, c in enumerate(chunks):
            if c in seen:
                collision = (seen[c], i)
                break
            seen[c] = i
        if collision is None:
            return chunks
        i, j = collision
        # Try to borrow from a third chunk that has headroom above floor.
        donors = [k for k in range(len(chunks))
                  if k != i and k != j and chunks[k] > floor + min_increment]
        if donors:
            d = rng.choice(donors)
            chunks[j] += min_increment
            chunks[d] -= min_increment
        elif chunks[i] >= floor + min_increment:
            # No third donor; shift one increment from i to j.
            chunks[i] -= min_increment
            chunks[j] += min_increment
        else:
            # Stuck — nothing has room above the floor.
            break
    return chunks
