"""mStock read-only connection.

Endpoints + header style ported from TradingBot/kickstart.py get_positions().
NOTE: verify the exact holdings endpoint + auth header against the live mStock
docs or the working TradingBot code before first real use — flagged, not assumed.
"""
import requests

from .base import Broker

BASE = "https://api.mstock.trade/openapi/typea"


class MStockBroker(Broker):
    broker = "mstock"

    def __init__(self, name, api_key, access_token):
        self.name = name
        self._headers = {
            "X-Mirae-Version": "1",
            "Authorization": f"token {api_key}:{access_token}",
        }

    def holdings(self):
        r = requests.get(f"{BASE}/portfolio/holdings", headers=self._headers,
                         timeout=(5, 15))
        r.raise_for_status()
        out = []
        for p in (r.json().get("data") or []):
            qty = float(p.get("quantity", 0) or 0)
            avg = float(p.get("average_price", 0) or 0)
            last = float(p.get("last_price", 0) or 0)
            invested = qty * avg
            pnl = (last - avg) * qty
            out.append({
                "symbol": p.get("tradingsymbol") or p.get("symbol", "?"),
                "qty": qty, "avg_price": avg, "last_price": last,
                "pnl": round(pnl, 2),
                "pnl_pct": round(pnl / invested * 100, 2) if invested else 0.0,
            })
        return out

    def positions(self):
        return []  # add when needed; holdings covers Phase 1
