import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import date
from typing import Optional

from dotenv import load_dotenv

from utils import safe

load_dotenv(".env.local")


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

    fy_end = None
    if af is not None and getattr(af, "columns", None) is not None and len(af.columns) > 0:
        try:
            fy_end = pd.to_datetime(max(af.columns)).date()
        except Exception:
            fy_end = None

    fiscal_meta = build_fiscal_year_metadata(fy_end)
    current_price = info.get("currentPrice") or info.get("regularMarketPrice")
    current_fy_eps = None
    next_fy_eps = None
    if eps_est is not None and not eps_est.empty:
        try:
            if "0y" in eps_est.index:
                v = eps_est.loc["0y", "avg"] if "avg" in eps_est.columns else None
                current_fy_eps = round(float(v), 2) if v and not np.isnan(float(v)) else None
            if "+1y" in eps_est.index:
                v = eps_est.loc["+1y", "avg"] if "avg" in eps_est.columns else None
                next_fy_eps = round(float(v), 2) if v and not np.isnan(float(v)) else None
        except Exception:
            pass

    info["forwardEps"] = current_fy_eps
    info["forwardPE"] = round(float(current_price) / float(current_fy_eps), 2) if current_price and current_fy_eps and current_fy_eps > 0 else None
    info["forwardEpsYear"] = fiscal_meta.get("current_year")
    info["forwardEpsNextYear"] = fiscal_meta.get("next_year")
    info["forwardMetricBasis"] = fiscal_meta.get("current_range")
    info["forwardMetricNextBasis"] = fiscal_meta.get("next_range")
    info["forwardEpsNext"] = next_fy_eps

    return {"info": info, "history": hist, "quarterly": qf, "annual": af, "eps_estimate": eps_est}


def get_eps_estimates(data):
    """Return current and next fiscal-year EPS estimates with labels and date ranges."""
    est = data.get("eps_estimate")
    info = data["info"]
    fiscal_meta = {
        "current_label": f"FY{safe(info, 'forwardEpsYear')}" if safe(info, "forwardEpsYear") else "Current FY",
        "next_label": f"FY{safe(info, 'forwardEpsNextYear')}" if safe(info, "forwardEpsNextYear") else "Next FY",
        "current_range": safe(info, "forwardMetricBasis"),
        "next_range": safe(info, "forwardMetricNextBasis"),
    }
    current_label = fiscal_meta.get("current_label")
    next_label = fiscal_meta.get("next_label")
    ncy_eps = None
    cy_eps = None
    if est is not None and not est.empty:
        try:
            if "0y" in est.index:
                v = est.loc["0y", "avg"] if "avg" in est.columns else None
                cy_eps = round(float(v), 2) if v and not np.isnan(float(v)) else None
            if "+1y" in est.index:
                v = est.loc["+1y", "avg"] if "avg" in est.columns else None
                ncy_eps = round(float(v), 2) if v and not np.isnan(float(v)) else None
        except Exception:
            pass
    if ncy_eps is None:
        ncy_eps = cy_eps

    return {
        "current_label": current_label,
        "current_eps": cy_eps,
        "current_range": fiscal_meta.get("current_range"),
        "next_label": next_label,
        "next_eps": ncy_eps,
        "next_range": fiscal_meta.get("next_range"),
    }


def _format_fiscal_range(start_date: date, end_date: date):
    return f"{start_date.year:04d}/{start_date.month:02d}-{end_date.year:04d}/{end_date.month:02d}"


def _fiscal_period_from_end(end_date: date):
    start_ts = pd.Timestamp(end_date) - pd.DateOffset(years=1) + pd.DateOffset(days=1)
    start_date = start_ts.date()
    return {
        "label": f"FY{end_date.year}",
        "year": end_date.year,
        "start_date": start_date,
        "end_date": end_date,
        "range": _format_fiscal_range(start_date, end_date),
    }
def build_fiscal_year_metadata(fiscal_year_end: Optional[date]):
    if fiscal_year_end is None:
        return {
            "current_label": "Current FY",
            "next_label": "Next FY",
            "current_year": None,
            "next_year": None,
            "current_range": None,
            "next_range": None,
        }

    today = date.today()
    current_end = fiscal_year_end
    while current_end <= today:
        current_end = (pd.Timestamp(current_end) + pd.DateOffset(years=1)).date()
    next_end = (pd.Timestamp(current_end) + pd.DateOffset(years=1)).date()

    current_period = _fiscal_period_from_end(current_end)
    next_period = _fiscal_period_from_end(next_end)

    return {
        "current_label": current_period["label"],
        "next_label": next_period["label"],
        "current_year": current_period["year"],
        "next_year": next_period["year"],
        "current_range": current_period["range"],
        "next_range": next_period["range"],
    }


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
