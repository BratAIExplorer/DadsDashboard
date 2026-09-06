"""Company news per watchlist stock.

Phase 0: Google News RSS per stock (reliable, no key, no cookies).
Phase 0.1 (backlog): add NSE/BSE official announcements as the primary source.
"""
import hashlib
import sqlite3
import time
import urllib.parse
from datetime import datetime, timezone, timedelta
from pathlib import Path

import feedparser

DB = Path(__file__).with_name("seen.sqlite")
IST = timezone(timedelta(hours=5, minutes=30))

MATERIAL = ("order", "wins", "awarded", "contract", "results", "profit", "loss",
            "dividend", "bonus", "split", "pledge", "qip", "fund rais", "acquisition",
            "acquire", "merger", "resign", "downgrade", "upgrade", "block deal",
            "bulk deal", "stake", "buyback", "board meeting")

POS = ("wins", "order", "awarded", "contract", "profit", "up ", "surge", "jump",
       "record", "beat", "upgrade", "buyback", "bonus")
NEG = ("loss", "pledge", "resign", "downgrade", "fall", "drop", "probe", "fraud",
       "penalty", "decline", "cut")


def _db():
    c = sqlite3.connect(DB)
    c.execute("CREATE TABLE IF NOT EXISTS seen(id TEXT PRIMARY KEY, ts REAL)")
    return c


def _sentiment(title):
    t = title.lower()
    if any(w in t for w in NEG):
        return "neg"
    if any(w in t for w in POS):
        return "pos"
    return "neu"


def _fetch_one(name, symbol):
    q = urllib.parse.quote(f'"{name}" when:2d')
    url = f"https://news.google.com/rss/search?q={q}&hl=en-IN&gl=IN&ceid=IN:en"
    out = []
    try:
        feed = feedparser.parse(url)
    except Exception:
        return out
    for e in feed.entries[:8]:
        title = e.get("title", "").strip()
        if not title:
            continue
        src = ""
        if " - " in title:
            title, src = title.rsplit(" - ", 1)
        uid = hashlib.sha1(f"{symbol}|{title}".encode()).hexdigest()
        low = title.lower()
        out.append({
            "id": uid, "symbol": symbol, "name": name, "head": title.strip(),
            "src": src.strip() or "Google News",
            "time": _pub(e), "cls": _sentiment(title),
            "important": any(w in low for w in MATERIAL),
        })
    return out


def _pub(entry):
    try:
        st = entry.published_parsed
        return datetime(*st[:6], tzinfo=timezone.utc).astimezone(IST).strftime("%d %b %H:%M")
    except Exception:
        return datetime.now(IST).strftime("%d %b %H:%M")


def fetch(stocks):
    """Returns (items_newest_first, ok). Only items not seen before are returned."""
    items, got_count = [], 0
    for s in stocks:
        got = _fetch_one(s["name"], s["symbol"])
        if got:
            got_count += 1
        items.extend(got)
    # "ok" = most stocks returned something (a few empty feeds is normal)
    ok = not stocks or got_count >= max(1, len(stocks) // 2)

    if not items:
        return [], ok

    con = _db()
    fresh = []
    for it in items:
        cur = con.execute("SELECT 1 FROM seen WHERE id=?", (it["id"],)).fetchone()
        if cur:
            continue
        con.execute("INSERT OR IGNORE INTO seen(id, ts) VALUES(?,?)", (it["id"], time.time()))
        fresh.append(it)
    con.commit()
    con.close()

    fresh.sort(key=lambda x: x["time"], reverse=True)
    return fresh, ok
