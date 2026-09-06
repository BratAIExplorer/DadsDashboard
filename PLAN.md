# Deepak's Market Board — Final Plan

*2026-09-06. Build spec. Brainstorm & design rules: see BRAINSTORM-dashboard.md.*

Accounts to connect: **2 Zerodha + 1 mStock.**

---

## 1. How the 3-account connection works

All 3 are just client objects in one Python program. The work is the daily login, not "parallel".

| Account | API | Cost | What you set up once | What happens each morning |
|---|---|---|---|---|
| Zerodha #1 | Kite Connect | ~₹500/mo | 1 developer app → `api_key` + `api_secret` | Log in on Zerodha's page → one-time token → today's access token (SHA-256 checksum). ~30 sec. |
| Zerodha #2 | Kite Connect | ~₹500/mo | **Separate** developer app → its own `api_key` + `api_secret` | Same, separately. ~30 sec. |
| mStock | mStock Trading API | Free | `api_key`, `api_secret`, `client_code`, `password`, `totp_secret` (reuse from TradingBot `settings.json`) | Auto TOTP login — no clicks. Code already exists in TradingBot. |

- **`accounts.yaml`** — 3 blocks (name, broker, api_key, api_secret, token-file path). Secrets encrypted with Fernet (reuse `settings_store.py`); `.encryption_key` gitignored.
- **`brokers/zerodha.py` + `brokers/mstock.py`** — each exposes the same 2 methods: `holdings()`, `positions()`. Dashboard never knows which broker it's talking to.
- **`login.py`** — run each morning. Does the 3 logins, writes 3 token files. mStock is automatic; each Zerodha needs a ~30-sec browser step (Zerodha blocks fully-headless login).
- **Dashboard** reads the 3 token files, loops the 3 accounts, merges holdings into one table with an `account` column.
- **Prices come from ONE source** (yfinance) — never fetched 3×. The broker clients are only for holdings / P&L / margin.

Money note: 2 Kite apps = **₹1,000/mo recurring**. Confirm before creating.

---

## 2. File layout (standalone, lite)

```
Deepaks-Bots/
  app.py                  # run this. builds data, serves localhost dashboard, writes Desktop files
  requirements.txt        # requests, pandas, yfinance, pyyaml, cryptography, openpyxl, kiteconnect
  my_stocks.txt           # the watchlist (also editable from the web box)
  export.py               # write board + news to Desktop\MarketBoard\*.csv / *.xlsx
  setup.html              # form to key in each account's credentials  (Phase 1)
  accounts.yaml           # 3 accounts, secrets encrypted   (Phase 1)
  .encryption_key         # gitignored                       (Phase 1)
  login.py                # morning: 3 logins -> token files  (Phase 1)
  brokers/
    base.py               # holdings(), positions()          (Phase 1)
    zerodha.py            #                                   (Phase 1)
    mstock.py             #                                   (Phase 1)
  data/
    prices.py             # yfinance quote + RSI + MACD + trend word
    news.py               # NSE/BSE announcements + Google News + tag + dedupe
  reuse/                  # trimmed copies from TradingBot, nothing else
    rsi.py               # TradingView-style RSI
    settings_store.py    # Fernet encrypt/decrypt for accounts.yaml
    telegram_send.py     # requests.post to api.telegram.org
    market_hours.py      # is_market_open_now_ist(), is_trading_day()
    mstock_holdings.py   # GET /portfolio/holdings parse       (Phase 1)
  templates/
    dashboard.html        # the big-font screen (from mockup.html)
  seen.sqlite             # news dedupe + alert log
```

Runs with `python app.py` on Dad's Windows laptop. Opens his browser at `localhost:8000`. No server to host, no Docker, no cloud.

---

## Status (2026-09-06)

- **Phase 0 — BUILT & VERIFIED.** `app.py` serves localhost:8000, 8 stocks with
  trend/RSI/MACD, Google-News feed, writes `board_latest` + `history` + `news_history`
  to `Desktop\MarketBoard\` every refresh. Smoke-tested against the real watchlist.
- **Phase 1 — SCAFFOLD BUILT & MOCK-VERIFIED.** `brokers/` (base, mock, zerodha,
  mstock), `brokers/merge.py` (holdings merge + watchlist cross-check), and
  `reuse/settings_store.py` (Fernet) all pass their self-tests with a fake broker.
  **Blocked on real credentials** — see §4.
- **Phase 2 — NOT STARTED.** Gated: no order code until Phase 1 has run read-only
  for weeks (money-risk rule).

## 3. Build phases

### Phase 0 — Trend + News board (no broker connection)
yfinance prices · RSI + MACD · trend word · NSE/BSE + Google News feed · big-font UI · add/remove stocks · **writes board + news to CSV/XLSX on the Desktop every 15 min.**
**Needs nothing from any broker.** Ship to Dad's laptop, run for a few days.

### Phase 1 — Add the 3 accounts, read-only
`setup.html` (key in credentials) + `brokers/` + `login.py` + `accounts.yaml`. Merge holdings from all 3 → per-stock: Held / Watching-only, qty, buy price, P&L, account. Desktop CSV/XLSX now includes the holdings columns. Stop-loss / averaging-down flags shown on screen. **No order code, no Telegram.** Run for weeks.

### Phase 2 — Order routing (later, maybe never)
Only after Phase 1 has proven itself. Placing trades across 3 accounts from one script is where mistakes cost money.

---

## 4. Next steps

**Bharat (setup — can't be automated):**
1. Create **2 separate Zerodha Kite Connect apps** (one per account) at `developers.kite.trade` → 2× `api_key` + `api_secret`. ₹500/mo each — **confirm you want this recurring cost.**
2. Confirm the **mStock** credentials for the 1 account (copy from `TradingBot\settings.json`: api_key, api_secret, client_code, password, totp_secret).
3. **Telegram:** create a bot via `@BotFather` → bot token + chat_id. Or decide "screen only, no phone alerts".
4. Give the **watchlist** — the 4–6 stocks Dad actually tracks.
5. Confirm **Python 3.10+** is on Dad's laptop (`python --version`).

**Me — done:**
6. ~~Phase 0 scaffold + real data~~ ✅ built & verified.
7. ~~Phase 1 broker scaffold + merge + encrypted store~~ ✅ built & mock-verified.

**Me — next, once you unblock §4 (using the 4 principles: state assumptions,
smallest change, verify each step):**
8. Add `/setup` page → writes encrypted `accounts.yaml`. *Verify: re-open page, values
   masked, decrypt round-trips.*
9. `login.py` — mStock TOTP auto + Zerodha one-click each. *Verify: 3 token files written,
   `holdings()` returns rows with no auth error.*
10. Wire `brokers/merge.py` into `app.py` — Held/Watching tags + P&L on the cards,
    holdings columns into `history.csv`. *Verify: a known holding shows correct qty/P&L
    vs the broker app.*
11. Run read-only for a few weeks. Only then discuss Phase 2.

---

## 5. Decisions (made 2026-09-06)

| Question | Decision |
|---|---|
| Phone alerts? | **Backlog.** No Telegram in Phase 0/1. Screen + file only. |
| Credentials | **Setup screen** in the dashboard: one form per account to key in `api_key`, `api_secret`, `client_code`, `password`, `totp_secret`. Saved encrypted to `accounts.yaml` (Fernet). Entered once, editable later. |
| Morning login | mStock = **fully automatic** (stored TOTP). Zerodha ×2 = **one click each** — the app opens the Kite login URL, Dad logs in on Zerodha's real page, done (~30 sec each). Full Zerodha auto-login → **backlog**. |
| Output | Every refresh writes the full board to **CSV and XLSX on the Desktop**: `Desktop\MarketBoard\board_YYYY-MM-DD.csv` + `.xlsx`. Columns: stock, trend, price, RSI, MACD, held?, qty, buy price, P&L, account. News to `news_YYYY-MM-DD.csv`. The web screen stays too. |
| Refresh speed | **Every 15 minutes** during market hours (09:15–15:30 IST) for prices / RSI / MACD / holdings. **News every hour** (runs on every 4th tick). Rationale below. |

### Why 15 minutes

- Free price data (yfinance) is itself delayed ~15 min — polling faster buys nothing real.
- Dad trades swing + hourly intraday, not scalping — 15-min granularity is plenty to catch a stop-loss breach or a trend flip.
- NSE/BSE announcements and Google News don't update usefully faster than hourly, and hourly keeps the feed quiet.
- One simple loop: refresh every 15 min; the news step only runs once an hour.

---

## 6. Backlog (not now)

- Telegram / phone alerts on "important" news and stop-loss breaches.
- Full Zerodha auto-login (store password + TOTP, script the login page). Fragile, revisit only if the daily click becomes a real annoyance.
- Order routing (this is Phase 2, listed above).
- Bulk/block deals + insider (PIT) disclosure feed.
- Paid news feed (Marketaux / Trendlyne) if free sources prove too slow.
