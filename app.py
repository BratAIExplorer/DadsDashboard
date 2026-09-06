"""Deepak's Market Board - Phase 0 (no broker connection).

Run:  python app.py
Opens http://127.0.0.1:8000 in the browser. Refreshes every 15 min during
market hours (09:15-15:30 IST, Mon-Fri), hourly otherwise. Writes CSV/XLSX to
Desktop\\MarketBoard every refresh.
"""
import threading
import time
import webbrowser
from datetime import datetime, timezone, timedelta

from flask import Flask, redirect, render_template, request

import data
import export
import news
import watchlist

IST = timezone(timedelta(hours=5, minutes=30))
app = Flask(__name__)

SNAP = {"ts": "not yet", "stocks": [], "news": [], "prices_ok": False,
        "news_ok": False, "out_dir": ""}
_lock = threading.Lock()
_last_news = 0.0


def market_open(now=None):
    now = now or datetime.now(IST)
    if now.weekday() >= 5:
        return False
    mins = now.hour * 60 + now.minute
    return 9 * 60 + 15 <= mins <= 15 * 60 + 30


def refresh(force_news=False):
    global _last_news
    stocks = watchlist.load()
    rows, prices_ok = data.fetch(stocks)

    do_news = force_news or (time.time() - _last_news > 3300)  # ~55 min
    if do_news:
        items, news_ok = news.fetch(stocks)
        _last_news = time.time()
    else:
        items, news_ok = [], SNAP["news_ok"]

    out_dir = export.write(rows, items)

    with _lock:
        SNAP["ts"] = datetime.now(IST).strftime("%d %b %Y  %I:%M %p")
        SNAP["stocks"] = rows
        SNAP["prices_ok"] = prices_ok
        SNAP["out_dir"] = out_dir
        if do_news:
            SNAP["news"] = (items + SNAP["news"])[:40]
            SNAP["news_ok"] = news_ok


def loop():
    while True:
        try:
            refresh()
        except Exception as e:  # keep the loop alive
            print("refresh error:", e)
        time.sleep(15 * 60 if market_open() else 60 * 60)


@app.route("/")
def home():
    with _lock:
        s = dict(SNAP)
    return render_template("dashboard.html", **s)


@app.route("/refresh", methods=["POST"])
def do_refresh():
    refresh(force_news=True)
    return redirect("/")


@app.route("/add", methods=["POST"])
def add():
    watchlist.add(request.form.get("symbol", ""), request.form.get("name", ""))
    refresh()
    return redirect("/")


@app.route("/remove", methods=["POST"])
def remove():
    watchlist.remove(request.form.get("symbol", ""))
    refresh()
    return redirect("/")


if __name__ == "__main__":
    print("Deepak's Market Board - starting, first data pull may take ~20s...")
    refresh(force_news=True)
    threading.Thread(target=loop, daemon=True).start()
    webbrowser.open("http://127.0.0.1:8000")
    app.run(host="127.0.0.1", port=8000, debug=False)
