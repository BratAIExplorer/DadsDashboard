"""A broker connection exposes exactly two read-only methods.

Phase 1 is read-only. No place_order here on purpose (YAGNI — that is Phase 2).

holdings() / positions() each return a list of:
    {symbol, qty, avg_price, last_price, pnl, pnl_pct}
"""


class Broker:
    name = "?"
    broker = "?"

    def holdings(self):
        raise NotImplementedError

    def positions(self):
        raise NotImplementedError
