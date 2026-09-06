"""Prices, RSI, MACD and a plain-English trend word for each watchlist stock.

Free data only (yfinance). No broker connection. ~15 min delayed — fine for a
swing / hourly board.
"""
import pandas as pd
import yfinance as yf

VERDICTS = {
    2:  {"key": "v-vbull", "big": "Very Bullish", "sub": "▲▲ strong up"},
    1:  {"key": "v-bull",  "big": "Bullish",      "sub": "▲ going up"},
    0:  {"key": "v-neut",  "big": "Neutral",      "sub": "● flat"},
    -1: {"key": "v-bear",  "big": "Bearish",      "sub": "▼ going down"},
    -2: {"key": "v-vbear", "big": "Very Bearish", "sub": "▼▼ strong down"},
}
NO_DATA = {"key": "v-neut", "big": "No data", "sub": "check symbol"}


def _rsi(close, n=14):
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    ag = gain.ewm(alpha=1 / n, min_periods=n, adjust=False).mean()
    al = loss.ewm(alpha=1 / n, min_periods=n, adjust=False).mean()
    rs = ag / al.replace(0, pd.NA)
    return 100 - 100 / (1 + rs)


def _macd(close):
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    macd = ema12 - ema26
    signal = macd.ewm(span=9, adjust=False).mean()
    return macd - signal  # histogram


def _rsi_word(v):
    if v is None:
        return ["Waiting for data", "mid"]
    if v < 30:
        return ["Oversold — looks cheap", "good"]
    if v < 45:
        return ["Weak", "mid"]
    if v <= 60:
        return ["Neutral", "mid"]
    if v <= 70:
        return ["Getting expensive", "mid"]
    return ["Overbought", "bad"]


def _macd_word(hist_now, hist_prev):
    if hist_now is None:
        return ["Waiting for data", "mid"]
    rising = hist_prev is not None and hist_now > hist_prev
    if abs(hist_now) < 1e-6:
        return ["Flat", "mid"]
    if hist_now > 0:
        return ["Rising — momentum up", "good"] if rising else ["Positive", "good"]
    return ["Falling — momentum down", "bad"] if not rising else ["Negative", "bad"]


def _one(symbol, name, df):
    if df is None or df.empty or len(df) < 30 or "Close" not in df:
        return {"symbol": symbol, "name": name, "price": "—", "chg": "", "dir": "up",
                "rsi": "—", "rsiW": ["Waiting for data", "mid"],
                "macdW": ["Waiting for data", "mid"], "verdict": NO_DATA,
                "held": False, "price_num": "", "chg_num": "", "rsi_num": "",
                "macd_hist": "", "trend_word": "No data", "trend_score": ""}

    close = df["Close"].dropna()
    last = float(close.iloc[-1])
    prev = float(close.iloc[-2]) if len(close) > 1 else last
    chg_pct = (last - prev) / prev * 100 if prev else 0.0

    rsi_series = _rsi(close)
    rsi_val = rsi_series.iloc[-1]
    rsi_val = None if pd.isna(rsi_val) else round(float(rsi_val))

    hist = _macd(close)
    h_now = None if pd.isna(hist.iloc[-1]) else float(hist.iloc[-1])
    h_prev = None if len(hist) < 2 or pd.isna(hist.iloc[-2]) else float(hist.iloc[-2])

    sma20 = close.rolling(20).mean().iloc[-1]
    sma50 = close.rolling(50).mean().iloc[-1]

    score = 0
    if not pd.isna(sma20):
        score += 1 if last > sma20 else -1
    if not pd.isna(sma20) and not pd.isna(sma50):
        score += 1 if sma20 > sma50 else -1
    if h_now is not None:
        score += 1 if h_now > 0 else -1
    if rsi_val is not None:
        score += 1 if rsi_val > 55 else (-1 if rsi_val < 45 else 0)

    bucket = 2 if score >= 3 else 1 if score >= 1 else 0 if score == 0 else -1 if score >= -2 else -2

    return {
        "symbol": symbol, "name": name,
        "price": f"₹{last:,.2f}",
        "chg": f"{chg_pct:+.1f}%",
        "dir": "up" if chg_pct >= 0 else "down",
        "rsi": rsi_val if rsi_val is not None else "—",
        "rsiW": _rsi_word(rsi_val),
        "macdW": _macd_word(h_now, h_prev),
        "verdict": VERDICTS[bucket],
        "held": False,
        # raw numbers for history.csv (not shown on screen)
        "price_num": round(last, 2),
        "chg_num": round(chg_pct, 2),
        "rsi_num": rsi_val if rsi_val is not None else "",
        "macd_hist": round(h_now, 4) if h_now is not None else "",
        "trend_word": VERDICTS[bucket]["big"],
        "trend_score": score,
    }


def fetch(stocks):
    """stocks: list of {symbol, name}. Returns (rows, ok)."""
    if not stocks:
        return [], True
    tickers = [s["symbol"] + ".NS" for s in stocks]
    try:
        raw = yf.download(tickers, period="6mo", interval="1d", group_by="ticker",
                          auto_adjust=True, progress=False, threads=True)
    except Exception:
        return [_one(s["symbol"], s["name"], None) for s in stocks], False

    rows, ok = [], True
    for s in stocks:
        tk = s["symbol"] + ".NS"
        try:
            df = raw[tk] if len(tickers) > 1 else raw
            if hasattr(df, "columns") and isinstance(df.columns, pd.MultiIndex):
                df = df.xs(tk, axis=1)
        except Exception:
            df = None
        row = _one(s["symbol"], s["name"], df)
        if row["price"] == "—":
            ok = False
        rows.append(row)
    return rows, ok
