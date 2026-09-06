"""Zerodha (Kite Connect) read-only connection. One instance per account.

Needs today's access_token (from login.py). api_key + access_token only —
never the password.
"""
from .base import Broker


class ZerodhaBroker(Broker):
    broker = "zerodha"

    def __init__(self, name, api_key, access_token):
        from kiteconnect import KiteConnect
        self.name = name
        self._k = KiteConnect(api_key=api_key)
        self._k.set_access_token(access_token)

    def holdings(self):
        out = []
        for h in self._k.holdings():
            qty = h.get("quantity", 0) + h.get("t1_quantity", 0)
            avg = h.get("average_price", 0.0)
            last = h.get("last_price", 0.0)
            invested = qty * avg
            pnl = (last - avg) * qty
            out.append({
                "symbol": h["tradingsymbol"], "qty": qty, "avg_price": avg,
                "last_price": last, "pnl": round(pnl, 2),
                "pnl_pct": round(pnl / invested * 100, 2) if invested else 0.0,
            })
        return out

    def positions(self):
        out = []
        for p in self._k.positions().get("net", []):
            if not p.get("quantity"):
                continue
            out.append({
                "symbol": p["tradingsymbol"], "qty": p["quantity"],
                "avg_price": p.get("average_price", 0.0),
                "last_price": p.get("last_price", 0.0),
                "pnl": round(p.get("pnl", 0.0), 2), "pnl_pct": 0.0,
            })
        return out
