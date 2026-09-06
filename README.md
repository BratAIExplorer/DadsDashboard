# Deepak's Market Board

One screen: trend, RSI, MACD and news for a watchlist of NSE stocks.
Phase 0 = free data only, no broker connection. Runs on a local Windows laptop.

Repo: https://github.com/BratAIExplorer/DadsDashboard
Standalone project — does not depend on any other bot. See `PLAN.md` for phases,
`BRAINSTORM-dashboard.md` for the design rules.

## Status

- **Phase 0** (this screen) — built and tested. Free data, no broker.
- **Phase 1** — broker scaffold in `brokers/`, mock-tested. Needs real credentials
  (2 Zerodha Kite Connect apps + 1 mStock) to go live.
- **Phase 2** (order routing) — not started, gated behind weeks of Phase 1 read-only use.

## First-time setup

1. Install **Python 3.11 or 3.12** from python.org (tick *Add python.exe to PATH*).
2. Open PowerShell in this folder and run:

   ```
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```

## Every day

```
.venv\Scripts\activate
python app.py
```

The board opens in the browser at `http://127.0.0.1:8000`.
Leave the window open — it refreshes every 15 minutes during market hours.
Close the window to stop it.

## What it writes

`Desktop\MarketBoard\`
- `board_latest.csv` / `.xlsx` — what things look like right now (open in Excel)
- `history.csv` / `.xlsx` — one row per stock per refresh, kept forever (for studying later)
- `news_history.csv` — every news headline seen

## Editing the watchlist

Either the **My Stocks** box on the page, or edit `my_stocks.txt` (one line per stock:
`SYMBOL | Company name`).

## Not in Phase 0 (see PLAN.md)

Broker connection (2 Zerodha + 1 mStock), positions & P&L, NSE/BSE official filings,
Telegram alerts. Those are Phase 1 / backlog.
