# Deepak's Trading Dashboard — Brainstorm

*Saved 2026-09-06. Still brainstorming — not a build plan yet.*

**Who it's for:** Deepak (Bharat's dad), senior citizen. Simple to use, simple to edit,
big fonts, bright colours. He looks at it every morning when the market opens.

## Hard constraints (do not break)

- **Standalone project.** Lives only in `Deepaks-Bots\`. No dependency on `TradingBot\`
  or the Arun zips. Does not import from them, does not share their `.venv`.
- **Copy only what's needed** from `TradingBot\`, file by file, into `Deepaks-Bots\reuse\`
  — RSI formula, Fernet settings store, Telegram send, mStock holdings fetch, market-hours
  helper. Not the bot engine, not the strategies, not the FastAPI backend, not the Next.js
  frontend. Rewrite/trim each copied file to what this dashboard uses.
- **Lite and simple.** Small number of small files. Minimal dependencies
  (`requests`, `pandas`, `yfinance`, `pyyaml`, `cryptography`, `kiteconnect`). No framework.
- **Runs on Dad's local laptop.** Plain `python app.py` → opens in his browser (localhost).
  No server to host, no Docker, no cloud. Windows-friendly.

**What it does:** One screen that tells him, per watchlist stock:
1. Trend — Very Bearish / Bearish / Neutral / Bullish / Very Bullish (words + colour)
2. Latest company news, plain English, newest on top
3. (Later) positions + P&L + stop-loss alerts from his broker accounts

---

## Senior-citizen design rules (every screen)

| Rule | Concrete number |
|---|---|
| Base font | **20px minimum**, headings 28–36px, never below 18px anywhere |
| Verdict text (Bullish/Bearish) | **32px bold**, coloured |
| Colours | Bright, high-contrast only: green `#00A651`, red `#E4002B`, amber `#FFB300`, on white |
| Colour never alone | Always a word or icon too (▲ Bullish / ▼ Bearish) — age-related colour-blindness is common |
| Row height | Tall, generous spacing, fewer rows per screen is fine |
| Buttons | Big, plain words ("Refresh now", "Add stock"), min 48px tall |
| One screen | Everything visible on load. No tabs, no menus, no scrolling to find the important bit |
| No jargon | "Company news" not "corporate announcements"; "Going up / down" alongside Bullish/Bearish |

---

## Making it dead simple to edit

The only thing Deepak should ever change is **the list of stocks**.

1. **"My Stocks" box on the dashboard** — type a name, click Add; click ✕ to remove.
   No file, no editor. **← Recommended, nothing to break.**
2. Google Sheet he edits from his phone; dashboard reads it each refresh.
3. Plain `stocks.txt`, one per line — rejected, means opening a file.

Everything else (news sources, timings, keywords) stays in code where he never sees it.

---

## News feed — technical shape

**Reality check:** true "as it breaks" (sub-minute) news for Indian smallcaps is a paid
feed + websocket, a separate project. For swing + hourly intraday, polling on the hourly
tick (≤1h lag) is enough.

| Source | Catches | Cost | Notes |
|---|---|---|---|
| **NSE / BSE company announcements** | Order wins, results, board meetings, pledges, QIP, resignations — price-sensitive, filed here first by law | Free | The one that matters for KERNEX/SUZLON-type names |
| **Google News RSS, one query per stock** | Moneycontrol / ET / BQ articles | Free, no key | `news.google.com/rss/search?q="Full Company Name"+when:1d`. Filter by full name + NSE symbol to kill collisions |
| **NSE bulk/block deals + insider (PIT) disclosures** | Promoter / big-holder buying or selling | Free | Weekly-ish, but a promoter dumping is real signal |
| Paid (later, if needed) | Marketaux / NewsAPI.ai / Trendlyne | ₹ | Skip for v1 |

**Do NOT hand-roll the NSE scraper.** `nseindia.com` blocks bare requests — needs a
homepage GET for cookies, reused session, browser-like headers, and it breaks on site
changes. Use a maintained lib: **`jugaad-data`** or **`nsepython`**. BSE is friendlier:
`https://api.bseindia.com/BseIndiaAPI/api/AnnGetData/w` works with a User-Agent header.

**Pipeline:**
- Cheap keyword pre-filter first (order/award/results/pledge/QIP/downgrade/block deal/
  resignation) — deterministic, works even if the LLM is down.
- Then **one** batched Haiku call per refresh (all new headlines together, not one call
  each) tags `bullish / bearish / neutral / material`.
- **SQLite `seen` table** for dedupe (NSE announcement ID; hash the title for Google
  News). Never re-alert, survives restarts.
- Dedupe across sources by `(symbol, date, title-keywords)` — same order win shows up in
  NSE + BSE + Google.
- Anything `material` also fires a **Telegram** alert: one `requests.post` to
  `api.telegram.org/bot<token>/sendMessage`, no library. Message = symbol, verdict,
  headline, source link.
- Skip PDF parsing — the headline text is enough to tag.
- **Never auto-trade on news. Context, not a signal.**

---

## Connecting Deepak's 3 trading accounts

He has **3 accounts** he wants connected. Broker mix TBD (originally discussed as
Zerodha + mStock — confirm which of the 3 is which).

It's just **3 client objects in one Python process.** The work is auth, not parallelism.

| Broker | API | Cost | Auth |
|---|---|---|---|
| Zerodha | Kite Connect — one API app per account | ~₹500/mo each | Daily login → access token, expires ~6 AM next day |
| mStock | mStock Trading API | Free | API key + daily session token (TOTP) per account |

**Shape:**
- `brokers/zerodha.py` + `brokers/mstock.py` — each exposes the same 4 methods:
  `positions()`, `holdings()`, `quote()`, (`place_order()` later).
- `accounts.yaml` — 3 entries (name, broker, api_key, secret, token-file path).
  Gitignore it; secrets in plaintext otherwise.
- Startup: loop the 3 → build 3 clients → pull positions + holdings → merge into one
  table with an `account` column.
- **Prices come from ONE source** (yfinance or a single Kite ticker), not fetched 3×.
  The 3 clients are only for account-specific data (holdings, P&L, margin).
- `login.py` — run each morning, does the 3 logins, writes 3 token files. Dashboard only
  reads them, keeping the fragile auth flow out of the main loop. `pyotp` automation
  optional; for a read-only dashboard, storing the TOTP secret is an acceptable
  trade-off — revisit before order-routing.
- Rate limits (Kite ~3 req/s) irrelevant at this cadence.

**Cadence:** positions poll **every 1–5 min** during market hours (well within limits) —
NOT hourly. A stop at ₹100 with the stock gapping ₹105→₹95 mid-hour = found out up to
60 min late = money. News + trend stay hourly.

**Phase it — money risk:**
1. **Read-only dashboard first.** Merge positions + P&L from the 3, show combined
   exposure, fire stop-loss / averaging-down / news alerts. Runs for weeks. No order code.
2. **Order routing later**, once phase 1 has proven itself.

**Prove the pipeline with ONE account before wiring all 3** — test the merge-to-one-table
logic on a single connection, then add the other 2 by editing `accounts.yaml`.

Note: trend + news need **zero broker connection** (free price data only). The broker
APIs are only for the positions / stop-loss panel. Ship the trend + news dashboard first,
add the 3 broker links after.

---

## Top 5 (weighted: core value · speed to validate · differentiation)

| # | Idea | Why | Test |
|---|---|---|---|
| **1** | Broker-free dashboard first — big fonts, bright verdicts, one screen | The whole promise, nothing blocks it, it's what he looks at every morning | Show Deepak a static mockup — can he read every number across the room? |
| **2** | "My Stocks" add/remove box, no files | The one edit he'll make; must be zero-friction | Watch him add a stock without help |
| **3** | NSE/BSE news via `jugaad-data`/`nsepython`, plain-English labels | Highest-risk piece; use a maintained lib | Do the libs pull fresh data today? |
| **4** | Keyword filter → batched Haiku tag → SQLite dedupe; only "important" news pings Telegram | Few, clear alerts he'll actually read | Hand-label 50 headlines vs Haiku |
| **5** | Positions poll 1–5 min (later phase, one account first) | Stop-loss alerts can't be an hour stale — money | Are his holds long enough that hourly is fine anyway? |

---

## Open questions

- Which 3 brokers exactly? (Zerodha ×? + mStock ×? + other?)
- How does Deepak actually trade — swing (days) or genuine hourly intraday? Decides
  whether 1–5 min position polling is needed or hourly is fine.
- Does free price data (yfinance / NSE quote) give a reliable trend read at 9:15 open?
  yfinance NSE intraday is patchy — compare vs Kite for a week.
- Telegram, or does he prefer WhatsApp / SMS / just the screen?
