"""Write the board to the Desktop every refresh.

  board_latest.csv / .xlsx   - current snapshot, overwritten (Dad opens this)
  history.csv / .xlsx        - one row per stock per refresh, appended forever
  news_history.csv           - news items, appended, deduped by id
"""
import csv
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pandas as pd

IST = timezone(timedelta(hours=5, minutes=30))
OUT = Path.home() / "Desktop" / "MarketBoard"

SNAP_COLS = ["symbol", "name", "trend_word", "price_num", "chg_num", "rsi_num",
             "macd_hist", "held", "qty", "buy_price", "pnl_rupees", "pnl_pct", "account"]
HIST_COLS = ["timestamp_ist"] + SNAP_COLS + ["trend_score"]
NEWS_COLS = ["timestamp_ist", "symbol", "name", "head", "src", "time", "cls", "important", "id"]


def _row(stock, now):
    return {
        "timestamp_ist": now,
        "symbol": stock["symbol"], "name": stock["name"],
        "trend_word": stock.get("trend_word", ""),
        "price_num": stock.get("price_num", ""),
        "chg_num": stock.get("chg_num", ""),
        "rsi_num": stock.get("rsi_num", ""),
        "macd_hist": stock.get("macd_hist", ""),
        "held": stock.get("held", False),
        "qty": stock.get("qty", ""),
        "buy_price": stock.get("avg", ""),
        "pnl_rupees": stock.get("pnl", ""),
        "pnl_pct": stock.get("pnlpct", ""),
        "account": stock.get("acct", ""),
        "trend_score": stock.get("trend_score", ""),
    }


def write(stocks, news):
    OUT.mkdir(parents=True, exist_ok=True)
    now = datetime.now(IST).strftime("%Y-%m-%d %H:%M")

    rows = [_row(s, now) for s in stocks]

    # 1. latest snapshot (overwrite)
    snap = pd.DataFrame(rows)[["timestamp_ist"] + SNAP_COLS + ["trend_score"]]
    snap.to_csv(OUT / "board_latest.csv", index=False)
    try:
        snap.to_excel(OUT / "board_latest.xlsx", index=False)
    except Exception:
        pass

    # 2. history (append)
    hist = OUT / "history.csv"
    new_file = not hist.exists()
    with hist.open("a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=HIST_COLS)
        if new_file:
            w.writeheader()
        w.writerows(rows)
    try:
        pd.read_csv(hist).to_excel(OUT / "history.xlsx", index=False)
    except Exception:
        pass

    # 3. news history (append; news items are already deduped upstream)
    if news:
        nf = OUT / "news_history.csv"
        new_file = not nf.exists()
        with nf.open("a", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=NEWS_COLS)
            if new_file:
                w.writeheader()
            for n in news:
                w.writerow({"timestamp_ist": now, **{k: n.get(k, "") for k in NEWS_COLS[1:]}})

    return str(OUT)
