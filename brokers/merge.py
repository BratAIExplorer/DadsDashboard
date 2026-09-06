"""Merge holdings from every account into one per-symbol view, and cross-check
against the watchlist.

    held_and_watched  - on the list AND owned  -> show position + trend + news
    watching_only     - on the list, not owned -> trend + news only
    held_not_watched  - owned, not on the list -> "you own this, add it?"
"""


def merge_holdings(brokers):
    by_symbol = {}
    for b in brokers:
        try:
            rows = b.holdings()
        except Exception as e:
            print(f"[{b.name}] holdings failed: {e}")
            rows = []
        for r in rows:
            by_symbol.setdefault(r["symbol"], []).append({**r, "account": b.name})
    return by_symbol


def cross_check(watchlist_symbols, by_symbol):
    held = set(by_symbol)
    wl = set(s.upper() for s in watchlist_symbols)
    return {
        "held_and_watched": sorted(held & wl),
        "watching_only": sorted(wl - held),
        "held_not_watched": sorted(held - wl),
    }


if __name__ == "__main__":
    from brokers.mock import MockBroker  # run:  python -m brokers.merge
    bs = [
        MockBroker("Zerodha Main", [
            {"symbol": "AVALON", "qty": 40, "avg_price": 465.0, "last_price": 512.4,
             "pnl": 1896.0, "pnl_pct": 10.2}]),
        MockBroker("mStock", [
            {"symbol": "KERNEX", "qty": 12, "avg_price": 1610.0, "last_price": 1486.0,
             "pnl": -1488.0, "pnl_pct": -7.7},
            {"symbol": "TATAPOWER", "qty": 50, "avg_price": 380.0, "last_price": 395.0,
             "pnl": 750.0, "pnl_pct": 3.9}]),
    ]
    merged = merge_holdings(bs)
    for sym, lots in merged.items():
        print(sym, "->", lots)
    print(cross_check(["AVALON", "KERNEX", "IDEA", "BSE"], merged))
    assert cross_check(["AVALON", "KERNEX", "IDEA"], merged)["held_not_watched"] == ["TATAPOWER"]
    assert "IDEA" in cross_check(["AVALON", "KERNEX", "IDEA"], merged)["watching_only"]
    print("merge: OK")
