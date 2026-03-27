import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import requests
import re
from datetime import datetime

from utils import safe


@st.cache_data(ttl=1800, show_spinner=False)
def fetch_data(symbol: str):
    t = yf.Ticker(symbol)

    try:
        info = t.info
    except Exception:
        info = {}

    # Enrich sparse info dict with fast_info fields (more reliable on cloud)
    try:
        fi = t.fast_info
        if not info.get("currentPrice") and not info.get("regularMarketPrice"):
            price = getattr(fi, "last_price", None) or getattr(fi, "regular_market_price", None)
            if price:
                info["currentPrice"] = float(price)
        if not info.get("previousClose"):
            prev = getattr(fi, "previous_close", None)
            if prev:
                info["previousClose"] = float(prev)
        if not info.get("marketCap"):
            mc = getattr(fi, "market_cap", None)
            if mc:
                info["marketCap"] = float(mc)
    except Exception:
        pass

    try:
        hist = t.history(period="3y")
    except Exception:
        hist = pd.DataFrame()

    qf = None
    try:
        qf = t.quarterly_income_stmt
    except Exception:
        pass

    af = None
    try:
        af = t.income_stmt          # annual — gives 4 fiscal years
    except Exception:
        pass

    eps_est = None
    try:
        eps_est = t.earnings_estimate
    except Exception:
        pass

    return {"info": info, "history": hist, "quarterly": qf, "annual": af, "eps_estimate": eps_est}


def get_eps_estimates(data):
    """Return {cy_label: eps, ncy_label: eps} from analyst estimates.

    Uses Yahoo's forwardEps (which backs their forwardPE) as the primary
    near-term estimate to avoid fiscal-year misalignment for companies whose
    year doesn't end in December (e.g. NVDA ends in January).
    """
    est = data.get("eps_estimate")
    info = data["info"]
    now = datetime.now()
    cy  = f"CY{now.year}"
    ncy = f"CY{now.year + 1}"

    # Primary: use Yahoo's own forwardEps for cy (same basis as their forwardPE)
    cy_eps = safe(info, "forwardEps")

    # For ncy use the analyst "+1y" estimate from earnings_estimate table
    ncy_eps = None
    if est is not None and not est.empty:
        try:
            if "+1y" in est.index:
                v = est.loc["+1y", "avg"] if "avg" in est.columns else None
                ncy_eps = round(float(v), 2) if v and not np.isnan(float(v)) else None
        except Exception:
            pass

    return {cy: cy_eps, ncy: ncy_eps}


def _strip_tz(idx):
    """Return a tz-naive DatetimeIndex."""
    if hasattr(idx, "tz") and idx.tz is not None:
        return idx.tz_localize(None)
    return idx


def build_quarterly_ttm_eps_series(data):
    """
    Build a point-in-time TTM EPS series from quarterly results only.

    Historical weekly P/E should only use true trailing four-quarter earnings.
    Carrying annual EPS forward across weekly prices materially distorts the
    denominator for names with sparse quarterly history.
    """
    qf = data.get("quarterly")
    info = data["info"]
    eps_points = {}

    if qf is not None and "Diluted EPS" in qf.index:
        try:
            eps_q = qf.loc["Diluted EPS"].dropna().sort_index()
            eps_q.index = _strip_tz(eps_q.index)
            dates = sorted(eps_q.index)
            for i in range(3, len(dates)):
                ttm_eps = float(eps_q.iloc[i - 3 : i + 1].sum())
                if ttm_eps > 0:
                    eps_points[dates[i]] = ttm_eps
        except Exception:
            pass

    if eps_points:
        return pd.Series(eps_points).sort_index()

    shares = safe(info, "sharesOutstanding")
    if not shares or shares <= 0:
        return None

    if qf is not None and "Net Income" in qf.index:
        try:
            ni_q = qf.loc["Net Income"].dropna().sort_index()
            ni_q.index = _strip_tz(ni_q.index)
            dates = sorted(ni_q.index)
            for i in range(3, len(dates)):
                ttm_eps = ni_q.iloc[i - 3 : i + 1].sum() / shares
                if ttm_eps > 0:
                    eps_points[dates[i]] = ttm_eps
        except Exception:
            pass

    return pd.Series(eps_points).sort_index() if eps_points else None


def build_ttm_eps_series(data):
    """
    Build a trailing EPS series.

    Prefer true quarterly TTM values. Fall back to annual EPS only when no
    quarterly TTM history is available, which is acceptable for spot valuation
    but not for historical weekly P/E.
    """
    eps_s = build_quarterly_ttm_eps_series(data)
    if eps_s is not None and not eps_s.empty:
        return eps_s

    af = data.get("annual")
    info = data["info"]
    eps_points = {}

    if af is not None and "Diluted EPS" in af.index:
        try:
            eps_a = af.loc["Diluted EPS"].dropna().sort_index()
            eps_a.index = _strip_tz(eps_a.index)
            for date, eps in eps_a.items():
                if eps > 0:
                    eps_points[date] = float(eps)
        except Exception:
            pass

    if eps_points:
        return pd.Series(eps_points).sort_index()

    shares = safe(info, "sharesOutstanding")
    if not shares or shares <= 0:
        return None

    if af is not None and "Net Income" in af.index:
        try:
            ni_a = af.loc["Net Income"].dropna().sort_index()
            ni_a.index = _strip_tz(ni_a.index)
            for date, ni in ni_a.items():
                if ni > 0:
                    eps_points[date] = ni / shares
        except Exception:
            pass

    return pd.Series(eps_points).sort_index() if eps_points else None


def normalize_eps_series_to_market_basis(data, eps_s):
    """
    Normalize statement-based EPS onto the traded share/currency basis.

    Some ADRs expose financial statements in the home-market currency/share
    basis while price and Yahoo's trailing EPS are reported on the ADR basis.
    Anchor the historical series to trailingEps when the currencies differ.
    """
    if eps_s is None or eps_s.empty:
        return eps_s

    info = data["info"]
    trade_ccy = safe(info, "currency")
    fin_ccy = safe(info, "financialCurrency")
    trailing_eps = safe(info, "trailingEps")

    if not trade_ccy or not fin_ccy or trade_ccy == fin_ccy or not trailing_eps:
        return eps_s

    latest_eps = eps_s.iloc[-1]
    if not latest_eps or latest_eps <= 0:
        return eps_s

    scale = float(trailing_eps) / float(latest_eps)
    if scale <= 0:
        return eps_s

    return eps_s * scale


@st.cache_data(ttl=1800, show_spinner=False)
def fetch_macrotrends_pe_history(symbol: str):
    """
    Fallback historical P/E source when Yahoo exposes only sparse quarterly EPS.

    Macrotrends redirects ticker URLs even with an incorrect slug, so the symbol
    alone is enough to resolve the company page.
    """
    url = f"https://www.macrotrends.net/stocks/charts/{symbol.upper()}/company/pe-ratio"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        resp = requests.get(url, headers=headers, timeout=10, allow_redirects=True)
        resp.raise_for_status()
    except Exception:
        return None

    table_match = re.search(
        r"<table[^>]*>.*?<th[^>]*>\s*Date\s*</th>.*?<th[^>]*>\s*PE Ratio\s*</th>.*?<tbody>(.*?)</tbody>",
        resp.text,
        re.IGNORECASE | re.DOTALL,
    )
    if not table_match:
        return None

    rows = re.findall(r"<tr>(.*?)</tr>", table_match.group(1), re.IGNORECASE | re.DOTALL)
    parsed = []
    for row in rows:
        cells = re.findall(r"<td[^>]*>\s*(.*?)\s*</td>", row, re.IGNORECASE | re.DOTALL)
        if len(cells) < 4:
            continue
        date_txt = re.sub(r"<.*?>", "", cells[0]).strip()
        pe_txt = re.sub(r"<.*?>", "", cells[3]).strip().replace(",", "")
        try:
            dt = pd.to_datetime(date_txt)
            pe = float(pe_txt)
        except Exception:
            continue
        if 3 < pe < 600:
            parsed.append({"date": dt, "pe": pe})

    if not parsed:
        return None

    df = pd.DataFrame(parsed).drop_duplicates(subset=["date"]).sort_values("date")
    return df.set_index("date")


def calc_pe_history(data):
    """Build trailing P/E history, preferring Yahoo quarterly TTM and falling back to Macrotrends."""
    hist = data["history"]

    if hist.empty:
        return None

    eps_s = build_quarterly_ttm_eps_series(data)
    if eps_s is None or eps_s.empty:
        return None
    eps_s = normalize_eps_series_to_market_basis(data, eps_s)

    # ── 3. Map onto weekly prices ─────────────────────────────────────────────
    weekly = hist["Close"].resample("W").last().dropna()
    rows = []
    for dt, price in weekly.items():
        dt_n = dt.tz_localize(None) if dt.tzinfo else dt
        avail = eps_s[eps_s.index <= dt_n]
        if avail.empty:
            continue
        e = avail.iloc[-1]
        if e > 0:
            pe = price / e
            if 3 < pe < 600:
                rows.append({"date": dt_n, "pe": round(pe, 2)})

    pe_df = pd.DataFrame(rows).set_index("date") if rows else None
    if pe_df is not None and not pe_df.empty:
        span_days = (pe_df.index.max() - pe_df.index.min()).days
        if span_days >= 700:
            return pe_df

    fallback_df = fetch_macrotrends_pe_history(safe(data["info"], "symbol", ""))
    if fallback_df is None or fallback_df.empty:
        return pe_df

    cutoff = hist.index.min().tz_localize(None) if getattr(hist.index, "tz", None) is not None else hist.index.min()
    return fallback_df[fallback_df.index >= cutoff]


def pe_stats(pe_df):
    if pe_df is None or pe_df.empty:
        return {}
    s = pe_df["pe"]
    return {
        "min": round(s.min(), 1),
        "max": round(s.max(), 1),
        "avg": round(s.mean(), 1),
        "std": round(s.std(), 1),
    }
