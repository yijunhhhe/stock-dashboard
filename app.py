"""
Stock Intelligence Dashboard
AI-powered valuation analysis using yfinance + Claude
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import anthropic
import json
import os
import re
import requests
import warnings
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(".env.local")

warnings.filterwarnings("ignore")

GROWTH_STORY_CACHE_PATH = Path(".cache/growth_story_cache.json")
GROWTH_STORY_CACHE_TTL_HOURS = 24
GROWTH_STORY_CACHE_MAX_ENTRIES = 100

# ─── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Stock Intelligence",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─── CSS ──────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  /* Global */
  .stApp {
    background:
      radial-gradient(circle at top left, rgba(43, 86, 173, 0.20), transparent 34%),
      radial-gradient(circle at top right, rgba(16, 185, 129, 0.12), transparent 28%),
      linear-gradient(180deg, #0b1020 0%, #0d1326 40%, #0b1020 100%);
  }
  .main .block-container { padding: 1.2rem 2rem 2.5rem; max-width: 1320px; }
  h1, h2, h3 { font-family: 'Avenir Next', 'Segoe UI', sans-serif; }
  #MainMenu, footer, header { visibility: hidden; }
  [data-testid="stVerticalBlock"] > [style*="flex-direction: column;"] > [data-testid="stVerticalBlock"] {
    gap: 0.35rem;
  }

  .app-shell {
    padding: 10px 0 6px;
  }
  .app-eyebrow {
    color: #7d8caf;
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    margin-bottom: 8px;
  }
  .app-title {
    color: #eef2ff;
    font-size: 2rem;
    font-weight: 800;
    letter-spacing: -0.04em;
    line-height: 1;
  }
  .app-subtitle {
    color: #8ea0c6;
    font-size: 0.95rem;
    margin-top: 8px;
    max-width: 680px;
    line-height: 1.5;
  }

  /* Metric cards */
  .card {
    background: linear-gradient(180deg, rgba(17, 24, 39, 0.84), rgba(13, 18, 31, 0.92));
    border: 1px solid rgba(63, 77, 112, 0.55);
    border-radius: 16px;
    padding: 16px 18px;
    margin-bottom: 10px;
    box-shadow: inset 0 1px 0 rgba(255,255,255,0.03);
  }
  .card-label {
    color: #8193bb;
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    margin-bottom: 6px;
  }
  .card-value {
    color: #edf2ff;
    font-size: 1.55rem;
    font-weight: 700;
    line-height: 1.1;
  }
  .card-sub {
    color: #4ade80;
    font-size: 0.82rem;
    margin-top: 4px;
    font-weight: 500;
  }
  .card-sub.down { color: #f87171; }
  .card-sub.neutral { color: #94a3b8; }

  /* Section headers */
  .section-title {
    color: #95a5c6;
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    border-bottom: 1px solid rgba(78, 92, 129, 0.55);
    padding-bottom: 9px;
    margin: 32px 0 18px;
  }
  .section-note {
    color: #8193bb;
    font-size: 0.88rem;
    line-height: 1.5;
    margin: -6px 0 12px;
    max-width: 760px;
  }

  /* AI insight card */
  .ai-shell {
    background: linear-gradient(180deg, rgba(12, 18, 33, 0.82), rgba(11, 16, 30, 0.94));
    border: 1px solid rgba(63, 77, 112, 0.52);
    border-radius: 18px;
    padding: 18px 20px;
    box-shadow: inset 0 1px 0 rgba(255,255,255,0.02);
  }
  .ai-grid {
    display: grid;
    grid-template-columns: minmax(0, 1.35fr) minmax(0, 1fr);
    gap: 14px;
  }
  .ai-block {
    background: rgba(255,255,255,0.02);
    border: 1px solid rgba(63, 77, 112, 0.42);
    border-radius: 14px;
    padding: 16px 18px;
    margin: 0;
  }
  .ai-badge {
    display: inline-block;
    background: rgba(148, 163, 184, 0.10);
    color: #99acd4;
    font-size: 0.68rem;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    padding: 5px 10px;
    border-radius: 20px;
    margin-bottom: 10px;
    border: 1px solid rgba(148,163,184,0.16);
  }
  .ai-method-name {
    color: #eef2ff;
    font-size: 1.2rem;
    font-weight: 700;
    margin-bottom: 6px;
  }
  .ai-reason { color: #9aaaca; font-size: 0.9rem; line-height: 1.55; }

  .hero-panel {
    background:
      linear-gradient(135deg, rgba(10, 18, 38, 0.95), rgba(14, 22, 42, 0.92)),
      radial-gradient(circle at top right, rgba(96,165,250,0.15), transparent 28%);
    border: 1px solid rgba(72, 88, 125, 0.6);
    border-radius: 24px;
    padding: 26px 28px;
    box-shadow:
      inset 0 1px 0 rgba(255,255,255,0.03),
      0 20px 60px rgba(2, 6, 23, 0.28);
  }
  .hero-meta {
    color: #7f90b6;
    font-size: 0.76rem;
    font-weight: 700;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    margin-bottom: 16px;
  }
  .ticker-name {
    font-size: 2.35rem;
    font-weight: 800;
    letter-spacing: -0.05em;
    color: #f8fbff;
    line-height: 1;
  }
  .ticker-meta {
    color: #8da0c7;
    font-size: 0.9rem;
    margin-top: 8px;
  }
  .price-row {
    display: flex;
    align-items: end;
    gap: 12px;
    margin-top: 18px;
    flex-wrap: wrap;
  }
  .price-big {
    font-size: 3rem;
    font-weight: 800;
    letter-spacing: -0.05em;
    color: #f3f6ff;
    line-height: 0.95;
  }
  .price-chg {
    font-size: 1rem;
    font-weight: 700;
    margin-left: 0;
    padding-bottom: 4px;
  }
  .hero-note {
    color: #7486ae;
    font-size: 0.86rem;
    margin-top: 10px;
  }
  .hero-stat-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 12px;
    height: 100%;
  }
  .hero-mini {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(72,88,125,0.5);
    border-radius: 16px;
    padding: 14px 16px;
  }
  .hero-mini-label {
    color: #7f90b6;
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    margin-bottom: 6px;
  }
  .hero-mini-value {
    color: #edf2ff;
    font-size: 1.25rem;
    font-weight: 700;
  }

  /* Catalyst tracker */
  .tracker-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    margin-bottom: 14px;
  }
  .tracker-title {
    color: #94a3b8;
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.14em;
    text-transform: uppercase;
  }
  .tracker-legend {
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
    justify-content: flex-end;
  }
  .tracker-pill {
    display: inline-flex;
    align-items: center;
    border-radius: 12px;
    padding: 8px 14px;
    font-size: 0.78rem;
    font-weight: 700;
    border: 1px solid;
    background: rgba(255,255,255,0.03);
  }
  .tracker-pill.priced-in { color: #f87171; border-color: rgba(248,113,113,0.45); background: rgba(127,29,29,0.22); }
  .tracker-pill.partial { color: #fbbf24; border-color: rgba(251,191,36,0.45); background: rgba(120,53,15,0.22); }
  .tracker-pill.not-priced-in { color: #4ade80; border-color: rgba(74,222,128,0.45); background: rgba(20,83,45,0.22); }
  .tracker-card {
    background: #161a23;
    border: 1px solid #2a303d;
    border-radius: 18px;
    padding: 18px 22px;
    margin-bottom: 12px;
    box-shadow: inset 0 0 0 1px rgba(255,255,255,0.02);
  }
  .tracker-card-top {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    margin-bottom: 10px;
  }
  .tracker-meta {
    display: flex;
    align-items: center;
    gap: 12px;
    flex-wrap: wrap;
  }
  .tracker-tag {
    display: inline-flex;
    align-items: center;
    border-radius: 10px;
    padding: 7px 14px;
    font-size: 0.78rem;
    font-weight: 700;
    border: 1px solid;
  }
  .tracker-tag.product { color: #60a5fa; border-color: rgba(96,165,250,0.35); background: rgba(30,64,175,0.20); }
  .tracker-tag.macro { color: #f59e0b; border-color: rgba(245,158,11,0.35); background: rgba(120,53,15,0.18); }
  .tracker-tag.business { color: #34d399; border-color: rgba(52,211,153,0.35); background: rgba(6,78,59,0.18); }
  .tracker-tag.risk { color: #f87171; border-color: rgba(248,113,113,0.35); background: rgba(127,29,29,0.18); }
  .tracker-timeframe {
    color: #64748b;
    font-size: 0.86rem;
  }
  .tracker-status {
    border-radius: 14px;
    padding: 10px 18px;
    font-size: 0.84rem;
    font-weight: 700;
    border: 1px solid;
    white-space: nowrap;
  }
  .tracker-status.priced-in { color: #f87171; border-color: rgba(248,113,113,0.45); background: rgba(127,29,29,0.22); }
  .tracker-status.partial { color: #fbbf24; border-color: rgba(251,191,36,0.45); background: rgba(120,53,15,0.22); }
  .tracker-status.not-priced-in { color: #4ade80; border-color: rgba(74,222,128,0.45); background: rgba(20,83,45,0.22); }
  .tracker-right {
    display: flex;
    align-items: center;
    gap: 10px;
    flex-wrap: wrap;
    justify-content: flex-end;
  }
  .tracker-direction {
    border-radius: 12px;
    padding: 8px 14px;
    font-size: 0.76rem;
    font-weight: 700;
    border: 1px solid;
    white-space: nowrap;
  }
  .tracker-direction.upside { color: #60a5fa; border-color: rgba(96,165,250,0.38); background: rgba(30,64,175,0.18); }
  .tracker-direction.downside { color: #f87171; border-color: rgba(248,113,113,0.38); background: rgba(127,29,29,0.18); }
  .tracker-group-title {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    margin: 14px 0 12px;
    font-size: 0.8rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
  }
  .tracker-group-title.upside { color: #60a5fa; }
  .tracker-group-title.downside { color: #f87171; }
  .tracker-headline {
    color: #f3f4f6;
    font-size: 1.08rem;
    font-weight: 700;
    line-height: 1.25;
    margin-bottom: 8px;
  }
  .tracker-detail {
    color: #8b93a6;
    font-size: 0.92rem;
    line-height: 1.5;
    max-width: 84%;
  }

  /* PE gauge bar */
  .pe-bar-container { margin: 16px 0; }
  .pe-bar-track {
    background: #1f2a45;
    border-radius: 99px;
    height: 8px;
    position: relative;
    overflow: visible;
  }
  .pe-bar-fill {
    height: 8px;
    border-radius: 99px;
    position: absolute;
    top: 0; left: 0;
  }
  .pe-bar-dot {
    width: 16px; height: 16px;
    border-radius: 50%;
    border: 2px solid white;
    position: absolute;
    top: -4px;
    transform: translateX(-50%);
  }

  /* Price target cards */
  .target-card {
    background: linear-gradient(180deg, rgba(17, 24, 39, 0.84), rgba(13, 18, 31, 0.94));
    border: 1px solid rgba(63, 77, 112, 0.55);
    border-radius: 16px;
    padding: 14px 16px;
    text-align: center;
  }
  .target-case { font-size: 0.68rem; font-weight: 700; letter-spacing: 0.12em; text-transform: uppercase; margin-bottom: 10px; }
  .target-price { font-size: 1.45rem; font-weight: 700; color: #e2e8f8; }
  .target-upside { font-size: 0.82rem; margin-top: 4px; font-weight: 700; }
  .target-pe { font-size: 0.75rem; color: #6b7db3; margin-top: 3px; }
  .target-label {
    color: #6f82ad;
    font-size: 0.66rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    margin-bottom: 4px;
  }

  /* Analyst target range bar */
  .at-shell {
    background: linear-gradient(180deg, rgba(17,24,39,0.84), rgba(13,18,31,0.92));
    border: 1px solid rgba(63,77,112,0.55);
    border-radius: 16px;
    padding: 16px 20px 18px;
    margin-top: 12px;
  }
  .at-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 14px;
  }
  .at-label {
    color: #8193bb;
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
  }
  .at-count {
    color: #4a5577;
    font-size: 0.72rem;
  }
  .at-rec {
    margin-left: auto;
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    padding: 4px 10px;
    border-radius: 8px;
    border: 1px solid;
  }
  .at-rec.strong-buy  { color: #4ade80; border-color: rgba(74,222,128,0.4); background: rgba(20,83,45,0.22); }
  .at-rec.buy         { color: #86efac; border-color: rgba(134,239,172,0.4); background: rgba(20,83,45,0.15); }
  .at-rec.hold        { color: #fbbf24; border-color: rgba(251,191,36,0.4);  background: rgba(120,53,15,0.22); }
  .at-rec.sell        { color: #f87171; border-color: rgba(248,113,113,0.4); background: rgba(127,29,29,0.22); }
  .at-rec.strong-sell { color: #f87171; border-color: rgba(248,113,113,0.4); background: rgba(127,29,29,0.28); }
  .at-bar-track {
    background: #1a2338;
    border-radius: 99px;
    height: 6px;
    position: relative;
    margin: 18px 0 8px;
  }
  .at-bar-fill {
    height: 6px;
    border-radius: 99px;
    background: linear-gradient(90deg, rgba(96,165,250,0.35), rgba(96,165,250,0.6));
    position: absolute;
    top: 0;
  }
  .at-dot-wrap {
    position: absolute;
    top: -4px;
    transform: translateX(-50%);
    cursor: pointer;
  }
  .at-dot {
    width: 14px; height: 14px;
    border-radius: 50%;
    border: 2px solid white;
  }
  .at-dot-wrap:hover .at-dot {
    width: 16px; height: 16px;
    margin: -1px;
  }
  .at-tooltip {
    display: none;
    position: absolute;
    bottom: 20px;
    left: 50%;
    transform: translateX(-50%);
    background: #1e2a40;
    color: #e2e8f0;
    font-size: 0.78rem;
    font-weight: 700;
    padding: 4px 9px;
    border-radius: 7px;
    border: 1px solid rgba(96,165,250,0.35);
    white-space: nowrap;
    pointer-events: none;
    box-shadow: 0 4px 12px rgba(0,0,0,0.4);
  }
  .at-tooltip::after {
    content: '';
    position: absolute;
    top: 100%; left: 50%;
    transform: translateX(-50%);
    border: 5px solid transparent;
    border-top-color: rgba(96,165,250,0.35);
  }
  .at-dot-wrap:hover .at-tooltip {
    display: block;
  }
  .at-mean-tick {
    width: 3px; height: 14px;
    border-radius: 2px;
    position: absolute;
    top: -4px;
    transform: translateX(-50%);
    background: #60a5fa;
  }
  .at-ticks {
    position: relative;
    height: 38px;
    margin-top: 10px;
  }
  .at-tick-group {
    position: absolute;
    text-align: center;
    transform: translateX(-50%);
  }
  .at-tick-group.left  { left: 0; transform: none; text-align: left; }
  .at-tick-group.right { right: 0; left: auto; transform: none; text-align: right; }
  .at-tick-price { color: #d8e0f5; font-size: 0.95rem; font-weight: 700; }
  .at-tick-label { color: #4a5577; font-size: 0.68rem; margin-top: 2px; }
  .at-upside {
    text-align: center;
    margin-top: 10px;
    font-size: 0.82rem;
    font-weight: 700;
  }

  /* Ticker header */
  @media (max-width: 900px) {
    .main .block-container { padding: 1rem 1rem 2rem; }
    .hero-panel { padding: 22px 18px; }
    .hero-stat-grid { grid-template-columns: 1fr 1fr; }
    .ai-grid { grid-template-columns: 1fr; }
    .price-big { font-size: 2.5rem; }
    .ticker-name { font-size: 2rem; }
    .tracker-detail { max-width: 100%; }
  }
</style>
""", unsafe_allow_html=True)


# ─── Helpers ──────────────────────────────────────────────────────────────────
def fmt_num(n, prefix="$"):
    if n is None or (isinstance(n, float) and np.isnan(n)):
        return "N/A"
    if abs(n) >= 1e12:
        return f"{prefix}{n/1e12:.2f}T"
    if abs(n) >= 1e9:
        return f"{prefix}{n/1e9:.2f}B"
    if abs(n) >= 1e6:
        return f"{prefix}{n/1e6:.2f}M"
    return f"{prefix}{n:,.1f}"


def fmt_pct(n):
    if n is None or (isinstance(n, float) and np.isnan(n)):
        return "N/A"
    return f"{n*100:+.1f}%"


def safe(d, key, default=None):
    v = d.get(key, default)
    if v is None:
        return default
    if isinstance(v, float) and np.isnan(v):
        return default
    return v


# ─── Data Fetching ────────────────────────────────────────────────────────────
@st.cache_data(ttl=1800, show_spinner=False)
def fetch_data(symbol: str):
    t = yf.Ticker(symbol)
    info = t.info
    hist = t.history(period="3y")

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
    """Return {cy_label: eps, ncy_label: eps} from analyst estimates."""
    est = data.get("eps_estimate")
    now = datetime.now()
    cy  = f"CY{now.year}"
    ncy = f"CY{now.year + 1}"
    result = {cy: None, ncy: None}

    if est is not None and not est.empty:
        try:
            # yfinance returns index with '0y' = current year, '+1y' = next year
            if "0y" in est.index:
                v = est.loc["0y", "avg"] if "avg" in est.columns else None
                result[cy] = round(float(v), 2) if v and not np.isnan(float(v)) else None
            if "+1y" in est.index:
                v = est.loc["+1y", "avg"] if "avg" in est.columns else None
                result[ncy] = round(float(v), 2) if v and not np.isnan(float(v)) else None
        except Exception:
            pass

    # Fallback to info fields if estimates missing
    if result[cy] is None:
        result[cy] = safe(data["info"], "trailingEps")
    if result[ncy] is None:
        result[ncy] = safe(data["info"], "forwardEps")

    return result


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


def load_growth_story_cache():
    if not GROWTH_STORY_CACHE_PATH.exists():
        return {}
    try:
        with GROWTH_STORY_CACHE_PATH.open("r", encoding="utf-8") as f:
            payload = json.load(f)
        return payload if isinstance(payload, dict) else {}
    except Exception:
        return {}


def save_growth_story_cache(cache):
    try:
        GROWTH_STORY_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        with GROWTH_STORY_CACHE_PATH.open("w", encoding="utf-8") as f:
            json.dump(cache, f)
    except Exception:
        pass


def prune_growth_story_cache(cache):
    now = datetime.utcnow()
    pruned = {}
    for key, entry in cache.items():
        if not isinstance(entry, dict):
            continue
        fetched_at = entry.get("fetched_at")
        if not fetched_at:
            continue
        try:
            age_hours = (now - datetime.fromisoformat(fetched_at)).total_seconds() / 3600
        except Exception:
            continue
        if age_hours <= GROWTH_STORY_CACHE_TTL_HOURS:
            pruned[key] = entry

    if len(pruned) <= GROWTH_STORY_CACHE_MAX_ENTRIES:
        return pruned

    ranked = sorted(
        pruned.items(),
        key=lambda item: item[1].get("last_accessed_at", item[1].get("fetched_at", "")),
        reverse=True,
    )
    return dict(ranked[:GROWTH_STORY_CACHE_MAX_ENTRIES])


def cache_key_for_growth_story(symbol):
    return f"v2:{symbol.upper().strip()}"


def get_cached_growth_story(symbol):
    cache = prune_growth_story_cache(load_growth_story_cache())
    key = cache_key_for_growth_story(symbol)
    entry = cache.get(key)
    if not entry:
        save_growth_story_cache(cache)
        return None

    entry["last_accessed_at"] = datetime.utcnow().isoformat()
    cache[key] = entry
    save_growth_story_cache(cache)
    return entry.get("story")


def set_cached_growth_story(symbol, story):
    cache = prune_growth_story_cache(load_growth_story_cache())
    now = datetime.utcnow().isoformat()
    cache[cache_key_for_growth_story(symbol)] = {
        "story": story,
        "fetched_at": now,
        "last_accessed_at": now,
    }
    save_growth_story_cache(prune_growth_story_cache(cache))


def invalidate_cached_growth_story(symbol):
    cache = load_growth_story_cache()
    key = cache_key_for_growth_story(symbol)
    if key in cache:
        del cache[key]
        save_growth_story_cache(prune_growth_story_cache(cache))


def cache_key_for_valuation_method(symbol):
    return f"valmethod:v1:{symbol.upper().strip()}"


def get_cached_valuation_method(symbol):
    cache = prune_growth_story_cache(load_growth_story_cache())
    key = cache_key_for_valuation_method(symbol)
    entry = cache.get(key)
    if not entry:
        save_growth_story_cache(cache)
        return None

    entry["last_accessed_at"] = datetime.utcnow().isoformat()
    cache[key] = entry
    save_growth_story_cache(cache)
    return entry.get("value")


def set_cached_valuation_method(symbol, value):
    cache = prune_growth_story_cache(load_growth_story_cache())
    now = datetime.utcnow().isoformat()
    cache[cache_key_for_valuation_method(symbol)] = {
        "value": value,
        "fetched_at": now,
        "last_accessed_at": now,
    }
    save_growth_story_cache(prune_growth_story_cache(cache))


def invalidate_cached_valuation_method(symbol):
    cache = load_growth_story_cache()
    key = cache_key_for_valuation_method(symbol)
    if key in cache:
        del cache[key]
        save_growth_story_cache(prune_growth_story_cache(cache))


def cache_key_for_pe_expectations(symbol):
    return f"peexpect:v2:{symbol.upper().strip()}"


def get_cached_pe_expectations(symbol):
    cache = prune_growth_story_cache(load_growth_story_cache())
    key = cache_key_for_pe_expectations(symbol)
    entry = cache.get(key)
    if not entry:
        save_growth_story_cache(cache)
        return None

    entry["last_accessed_at"] = datetime.utcnow().isoformat()
    cache[key] = entry
    save_growth_story_cache(cache)
    return entry.get("value")


def set_cached_pe_expectations(symbol, value):
    cache = prune_growth_story_cache(load_growth_story_cache())
    now = datetime.utcnow().isoformat()
    cache[cache_key_for_pe_expectations(symbol)] = {
        "value": value,
        "fetched_at": now,
        "last_accessed_at": now,
    }
    save_growth_story_cache(prune_growth_story_cache(cache))


def invalidate_cached_pe_expectations(symbol):
    cache = load_growth_story_cache()
    key = cache_key_for_pe_expectations(symbol)
    if key in cache:
        del cache[key]
        save_growth_story_cache(prune_growth_story_cache(cache))


# ─── Claude Calls ─────────────────────────────────────────────────────────────
def claude_valuation_method(client, info):
    ctx = f"""
Company: {safe(info,'longName', safe(info,'shortName','?'))}
Sector: {safe(info,'sector','?')} | Industry: {safe(info,'industry','?')}
Market Cap: {fmt_num(safe(info,'marketCap'))}
Profit Margin: {fmt_pct(safe(info,'profitMargins'))} | Op Margin: {fmt_pct(safe(info,'operatingMargins'))}
Revenue Growth YoY: {fmt_pct(safe(info,'revenueGrowth'))} | Earnings Growth: {fmt_pct(safe(info,'earningsGrowth'))}
Trailing P/E: {safe(info,'trailingPE','N/A')} | Forward P/E: {safe(info,'forwardPE','N/A')}
EV/EBITDA: {safe(info,'enterpriseToEbitda','N/A')} | P/S: {safe(info,'priceToSalesTrailing12Months','N/A')}
P/B: {safe(info,'priceToBook','N/A')} | FCF: {fmt_num(safe(info,'freeCashflow'))}
Debt/Equity: {safe(info,'debtToEquity','N/A')} | ROE: {fmt_pct(safe(info,'returnOnEquity'))}
Dividend Yield: {fmt_pct(safe(info,'dividendYield'))}
Business: {safe(info,'longBusinessSummary','')[:400]}
"""
    resp = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=500,
        messages=[{
            "role": "user",
            "content": f"""You are a senior equity analyst. Based on this company's profile, recommend the single BEST primary valuation method and optionally a secondary method.

{ctx}

Reply ONLY with valid JSON (no markdown, no extra text):
{{
  "primary": "PE" | "EV/EBITDA" | "P/S" | "P/FCF" | "P/B",
  "primary_reason": "2-3 sentences why this method suits this company",
  "secondary": "PE" | "EV/EBITDA" | "P/S" | "P/FCF" | "P/B" | null,
  "secondary_reason": "1 sentence or null"
}}"""
        }]
    )
    try:
        return json.loads(resp.content[0].text.strip())
    except Exception:
        return {"primary": "PE", "primary_reason": "Standard earnings-based valuation.", "secondary": None, "secondary_reason": None}


def claude_growth_story(client, info, stats, current_pe):
    vs_avg = ""
    if current_pe and stats.get("avg"):
        pct = (current_pe / stats["avg"] - 1) * 100
        direction = "premium" if pct > 0 else "discount"
        vs_avg = f"Trading at a {abs(pct):.1f}% {direction} to its 3-year average PE of {stats['avg']}x"

    prompt = f"""You are a top-tier equity analyst building a catalyst and expectations tracker for {safe(info,'longName','this company')}.

Key facts:
- Sector: {safe(info,'sector','?')} | Industry: {safe(info,'industry','?')}
- Market Cap: {fmt_num(safe(info,'marketCap'))}
- Revenue Growth: {fmt_pct(safe(info,'revenueGrowth'))} | Earnings Growth: {fmt_pct(safe(info,'earningsGrowth'))}
- Gross Margin: {fmt_pct(safe(info,'grossMargins'))} | FCF: {fmt_num(safe(info,'freeCashflow'))}
- Current PE: {current_pe:.1f}x | Forward PE: {safe(info,'forwardPE','N/A')}x
- {vs_avg}
- Analyst target: ${safe(info,'targetMeanPrice','N/A')} (low ${safe(info,'targetLowPrice','N/A')}, high ${safe(info,'targetHighPrice','N/A')})
- Recommendation: {safe(info,'recommendationKey','N/A')}
- Beta: {safe(info,'beta','N/A')} | 52W range: ${safe(info,'fiftyTwoWeekLow','N/A')} – ${safe(info,'fiftyTwoWeekHigh','N/A')}

Return ONLY valid JSON as an array with exactly 5 items, sorted by importance.
Each item must follow this schema:
[
  {{
    "type": "Product" | "Macro" | "Business" | "Risk",
    "timeframe": "0-6m" | "3-9m" | "6-18m" | "12-24m",
    "direction": "Upside" | "Downside",
    "headline": "5-7 words max",
    "detail": "1 short sentence, 8-18 words",
    "status": "Priced In" | "Partial" | "Not Priced In"
  }}
]

Rules:
- Tie each item to valuation expectations.
- Keep the language concrete, not promotional.
- Include at least 1 risk.
- Risks should almost always be "Downside".
- Prefer distinct items, not overlaps.
- No markdown, no commentary, no prose outside JSON."""

    with client.messages.stream(
        model="claude-sonnet-4-6",
        max_tokens=1200,
        messages=[{"role": "user", "content": prompt}]
    ) as stream:
        return stream.get_final_text()


def claude_pe_expectations(client, info, stats, current_pe, current_price, forward_eps, pe_history):
    history_lines = []
    if pe_history is not None and not pe_history.empty:
        sample = pe_history.tail(8)
        for dt, row in sample.iterrows():
            history_lines.append(f"- {dt.strftime('%Y-%m-%d')}: {row['pe']:.1f}x")
    history_block = "\n".join(history_lines) if history_lines else "- No usable historical PE points"
    price_text = f"${current_price:.2f}" if current_price else "N/A"
    trailing_pe_text = f"{current_pe:.1f}x" if current_pe else "N/A"
    forward_eps_text = f"${forward_eps:.2f}" if forward_eps else "N/A"

    prompt = f"""You are a top-tier equity analyst explaining valuation expectations through a P/E lens for {safe(info,'longName','this company')}.

Key facts:
- Current price: {price_text}
- Current trailing PE: {trailing_pe_text}
- Forward PE: {safe(info,'forwardPE','N/A')}x
- Forward EPS: {forward_eps_text}
- 3yr PE low / avg / high: {stats.get('min','N/A')}x / {stats.get('avg','N/A')}x / {stats.get('max','N/A')}x
- Revenue growth: {fmt_pct(safe(info,'revenueGrowth'))}
- Earnings growth: {fmt_pct(safe(info,'earningsGrowth'))}
- Gross margin: {fmt_pct(safe(info,'grossMargins'))}
- Operating margin: {fmt_pct(safe(info,'operatingMargins'))}
- FCF: {fmt_num(safe(info,'freeCashflow'))}
- Analyst target mean: ${safe(info,'targetMeanPrice','N/A')}
- Recommendation: {safe(info,'recommendationKey','N/A')}

Recent PE history points:
{history_block}

Return ONLY valid JSON with this schema:
{{
  "priced_in": {{
    "headline": "6-10 words",
    "bullets": ["bullet 1", "bullet 2", "bullet 3"]
  }},
  "pe_up": {{
    "headline": "6-10 words",
    "bullets": ["bullet 1", "bullet 2", "bullet 3"]
  }},
  "pe_down": {{
    "headline": "6-10 words",
    "bullets": ["bullet 1", "bullet 2", "bullet 3"]
  }}
}}

Rules:
- Focus on multiple expansion/compression, not just EPS changes.
- Mention guidance style explicitly when relevant: for example stronger duration, margin durability, backlog visibility, capex discipline, or downside guide.
- Keep language concrete and investor-facing.
- Each section must have exactly 3 bullets.
- Each bullet should be short, ideally 6-14 words.
- No markdown, no bullets, no prose outside JSON."""

    resp = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=700,
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.content[0].text.strip()


def extract_json_payload(text):
    """Extract a JSON object or array from Claude text output."""
    if not text:
        raise ValueError("Empty response")
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    match = re.search(r"(\{.*\}|\[.*\])", text, re.DOTALL)
    if not match:
        raise ValueError("No JSON payload found")
    return match.group(1)


def parse_pe_expectations(text):
    try:
        payload = json.loads(extract_json_payload(text))
    except Exception:
        return None

    if not isinstance(payload, dict):
        return None

    sections = {}
    for key in ["priced_in", "pe_up", "pe_down"]:
        item = payload.get(key)
        if not isinstance(item, dict):
            return None
        headline = str(item.get("headline", "")).strip()
        bullets = item.get("bullets", [])
        if not isinstance(bullets, list):
            return None
        cleaned_bullets = [str(b).strip() for b in bullets if str(b).strip()]
        if not headline or not cleaned_bullets:
            return None
        sections[key] = {"headline": headline, "bullets": cleaned_bullets[:3]}

    return sections


def render_pe_expectations(text):
    sections = parse_pe_expectations(text)
    if not sections:
        st.markdown(text)
        return

    cards = [
        ("priced_in", "Already Priced In", "#60a5fa"),
        ("pe_up", "What Pushes P/E Higher", "#34d399"),
        ("pe_down", "What Pushes P/E Lower", "#f97316"),
    ]

    cols = st.columns(3)
    for col, (key, badge, color) in zip(cols, cards):
        item = sections[key]
        bullet_html = "".join(f"<li>{b}</li>" for b in item["bullets"])
        with col:
            st.markdown(
                f'<div class="ai-block" style="height:100%;border-top:3px solid {color}">'
                f'  <div class="ai-badge">{badge}</div>'
                f'  <div class="ai-method-name" style="font-size:1rem">{item["headline"]}</div>'
                f'  <div class="ai-reason"><ul style="margin:0.35rem 0 0 1rem;padding:0">{bullet_html}</ul></div>'
                f'</div>',
                unsafe_allow_html=True,
            )


def parse_growth_story_items(story_text):
    try:
        payload = json.loads(extract_json_payload(story_text))
    except Exception:
        return []

    if not isinstance(payload, list):
        return []

    items = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        headline = str(item.get("headline", "")).strip()
        detail = str(item.get("detail", "")).strip()
        status = str(item.get("status", "")).strip()
        kind = str(item.get("type", "")).strip()
        timeframe = str(item.get("timeframe", "")).strip()
        direction = str(item.get("direction", "")).strip()
        if headline and detail and status and kind and timeframe and direction:
            items.append({
                "headline": headline,
                "detail": detail,
                "status": status,
                "type": kind,
                "timeframe": timeframe,
                "direction": direction,
            })
    return items


def render_growth_story(story_text):
    items = parse_growth_story_items(story_text)
    if not items:
        st.markdown(story_text)
        return

    pill_classes = {
        "Priced In": "priced-in",
        "Partial": "partial",
        "Not Priced In": "not-priced-in",
    }
    direction_classes = {
        "Upside": "upside",
        "Downside": "downside",
    }
    type_classes = {
        "Product": "product",
        "Macro": "macro",
        "Business": "business",
        "Risk": "risk",
    }

    st.markdown(
        '<div class="tracker-head">'
        '  <div class="tracker-title">Catalyst &amp; News Tracker</div>'
        '  <div class="tracker-legend">'
        '    <span class="tracker-pill priced-in">Priced In</span>'
        '    <span class="tracker-pill partial">Partial</span>'
        '    <span class="tracker-pill not-priced-in">Not Priced In</span>'
        '  </div>'
        '</div>',
        unsafe_allow_html=True,
    )

    grouped = {
        "Upside": [item for item in items if item["direction"] == "Upside"],
        "Downside": [item for item in items if item["direction"] == "Downside"],
    }

    for direction, direction_items in grouped.items():
        if not direction_items:
            continue

        direction_cls = direction_classes.get(direction, "upside")
        st.markdown(
            f'<div class="tracker-group-title {direction_cls}">{direction}</div>',
            unsafe_allow_html=True,
        )

        for item in direction_items:
            type_cls = type_classes.get(item["type"], "business")
            status_cls = pill_classes.get(item["status"], "partial")
            st.markdown(
                f'<div class="tracker-card">'
                f'  <div class="tracker-card-top">'
                f'    <div class="tracker-meta">'
                f'      <span class="tracker-tag {type_cls}">{item["type"]}</span>'
                f'      <span class="tracker-timeframe">{item["timeframe"]}</span>'
                f'    </div>'
                f'    <div class="tracker-right">'
                f'      <span class="tracker-status {status_cls}">{item["status"]}</span>'
                f'    </div>'
                f'  </div>'
                f'  <div class="tracker-headline">{item["headline"]}</div>'
                f'  <div class="tracker-detail">{item["detail"]}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )


# ─── Charts ───────────────────────────────────────────────────────────────────
def chart_pe_history(pe_df, stats, current_pe):
    fig = go.Figure()

    # Shaded range band
    if stats.get("min") and stats.get("max"):
        fig.add_hrect(
            y0=stats["min"], y1=stats["max"],
            fillcolor="rgba(59,130,246,0.05)",
            line_width=0,
        )

    # PE area line — fill to the bottom of the visible range, not zero
    y_min = pe_df["pe"].min() * 0.88
    fig.add_trace(go.Scatter(
        x=pe_df.index, y=pe_df["pe"],
        mode="lines",
        name="Trailing P/E",
        line=dict(color="#60a5fa", width=2),
        fill="toself",
        fillcolor="rgba(96,165,250,0.10)",
    ))
    # Invisible baseline so fill looks correct
    fig.add_trace(go.Scatter(
        x=[pe_df.index[0], pe_df.index[-1]],
        y=[y_min, y_min],
        mode="lines",
        line=dict(width=0),
        showlegend=False,
        hoverinfo="skip",
    ))

    # 3yr average
    if stats.get("avg"):
        fig.add_hline(
            y=stats["avg"],
            line_dash="dot",
            line_color="#34d399",
            annotation_text=f"  3yr avg {stats['avg']}x",
            annotation_font_color="#34d399",
            annotation_font_size=11,
        )

    # Current PE
    if current_pe:
        color = "#f87171" if current_pe > stats.get("avg", current_pe) * 1.1 else "#fbbf24" if current_pe > stats.get("avg", current_pe) else "#4ade80"
        fig.add_hline(
            y=current_pe,
            line_color=color,
            line_width=2,
            annotation_text=f"  Now {current_pe:.1f}x",
            annotation_font_color=color,
            annotation_font_size=12,
        )

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=280,
        margin=dict(l=10, r=90, t=16, b=10),
        showlegend=False,
        xaxis=dict(showgrid=False, color="#6b7db3", tickfont=dict(size=10)),
        yaxis=dict(
            showgrid=True,
            gridcolor="rgba(255,255,255,0.06)",
            color="#6b7db3",
            tickfont=dict(size=10),
            title="P/E Ratio",
            range=[pe_df["pe"].min() * 0.88, pe_df["pe"].max() * 1.10],
        ),
        hovermode="x unified",
    )
    return fig


def chart_price_targets(current_price, scenarios_cy, scenarios_ncy, cy_label, ncy_label, metric_label):
    """Waterfall-style grouped bar showing bear/base/bull for CY and NCY."""
    cases = ["Bear", "Base", "Bull"]
    colors_cy  = ["#f97316", "#60a5fa", "#34d399"]
    colors_ncy = ["#ea580c", "#3b82f6", "#22c55e"]

    fig = go.Figure()

    cy_prices  = [s["price"] for s in scenarios_cy]
    ncy_prices = [s["price"] for s in scenarios_ncy]
    cy_labels  = [f"${p:.0f}<br><span style='font-size:10px;color:#94a3b8'>{s['upside']:+.0f}%</span>"
                  for p, s in zip(cy_prices, scenarios_cy)]
    ncy_labels = [f"${p:.0f}<br><span style='font-size:10px;color:#94a3b8'>{s['upside']:+.0f}%</span>"
                  for p, s in zip(ncy_prices, scenarios_ncy)]

    fig.add_trace(go.Bar(
        name=cy_label, x=cases, y=cy_prices,
        marker_color=colors_cy,
        text=[f"${p:.0f}" for p in cy_prices],
        textposition="outside",
        textfont=dict(color="#e2e8f8", size=13, family="monospace"),
        width=0.35,
        offset=-0.2,
    ))

    fig.add_trace(go.Bar(
        name=ncy_label, x=cases, y=ncy_prices,
        marker_color=colors_ncy,
        text=[f"${p:.0f}" for p in ncy_prices],
        textposition="outside",
        textfont=dict(color="#e2e8f8", size=13, family="monospace"),
        width=0.35,
        offset=0.2,
    ))

    # Current price line
    fig.add_hline(
        y=current_price,
        line_dash="dash", line_color="#94a3b8", line_width=1.5,
        annotation_text=f"  Current ${current_price:.2f}",
        annotation_font_color="#94a3b8", annotation_font_size=11,
    )

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=360,
        barmode="overlay",
        bargap=0.35,
        margin=dict(l=10, r=40, t=40, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                    font=dict(color="#94a3b8", size=11)),
        xaxis=dict(tickfont=dict(size=12, color="#94a3b8"), showgrid=False),
        yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)",
                   tickfont=dict(size=10, color="#6b7db3"), title="Implied Price (USD)"),
        title=dict(text=f"Price Targets — {metric_label} Method", font=dict(color="#94a3b8", size=12), x=0),
    )
    return fig


def compute_targets(eps_cy, eps_ncy, stats, current_price):
    """Bear/base/bull price targets from min/avg/max PE."""
    bear_pe = stats.get("min")
    base_pe = stats.get("avg")
    bull_pe = stats.get("max")

    def scenario(eps, pe):
        if not eps or not pe or eps <= 0:
            return None
        price = eps * pe
        upside = (price / current_price - 1) * 100
        return {"price": price, "upside": upside, "pe": pe}

    return (
        [s for s in [scenario(eps_cy, bear_pe), scenario(eps_cy, base_pe), scenario(eps_cy, bull_pe)] if s],
        [s for s in [scenario(eps_ncy, bear_pe), scenario(eps_ncy, base_pe), scenario(eps_ncy, bull_pe)] if s],
    )




# ─── Metric Card HTML ─────────────────────────────────────────────────────────
def card(label, value, sub=None, sub_class=""):
    sub_html = f'<div class="card-sub {sub_class}">{sub}</div>' if sub else ""
    return f"""
<div class="card">
  <div class="card-label">{label}</div>
  <div class="card-value">{value}</div>
  {sub_html}
</div>"""


# ─── Main App ─────────────────────────────────────────────────────────────────
def main():
    st.markdown(
        '<div class="app-shell">'
        '  <div class="app-eyebrow">Equity Intelligence Surface</div>'
        '  <div class="app-title">Stock Intelligence</div>'
        '  <div class="app-subtitle">A compact valuation workspace for multiple compression, expectation mapping, and scenario framing.</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    # ── Input row ──
    if "active_symbol" not in st.session_state:
        st.session_state["active_symbol"] = "AAPL"
    if "_ticker_field" not in st.session_state:
        st.session_state["_ticker_field"] = st.session_state["active_symbol"]

    with st.form("ticker_form", border=False):
        c1, c2, c3 = st.columns([2, 1, 5])
        with c1:
            ticker_input = st.text_input("Ticker", key="_ticker_field", placeholder="e.g. AAPL", label_visibility="collapsed").upper().strip()
        with c2:
            go_btn = st.form_submit_button("Analyze →", type="primary", use_container_width=True)
        with c3:
            st.markdown(
                '<span style="color:#6b7db3;font-size:0.85rem;line-height:2.4rem;display:block">'
                'Try: AAPL · MSFT · NVDA · GOOGL · META · AMZN · TSLA</span>',
                unsafe_allow_html=True,
            )

    if go_btn and ticker_input:
        st.session_state["active_symbol"] = ticker_input

    symbol = st.session_state["active_symbol"]
    if not symbol:
        return

    # ── Fetch ──
    with st.spinner(f"Loading {symbol}…"):
        data = fetch_data(symbol)

    info = data["info"]
    if not info or not safe(info, "regularMarketPrice") and not safe(info, "currentPrice"):
        st.error(f"No data found for **{symbol}**. Please check the ticker symbol.")
        return

    current_price = safe(info, "currentPrice") or safe(info, "regularMarketPrice")
    prev_close    = safe(info, "previousClose") or current_price
    day_chg_pct   = (current_price / prev_close - 1) if prev_close else 0
    company_name  = safe(info, "longName") or safe(info, "shortName") or symbol
    sector        = safe(info, "sector", "")
    industry      = safe(info, "industry", "")
    exchange      = safe(info, "exchange", "")

    # ── Company header ──
    st.markdown('<div class="section-title">Company Overview</div>', unsafe_allow_html=True)
    hc1, hc3 = st.columns([5, 3])

    with hc1:
        chg_color = "#4ade80" if day_chg_pct >= 0 else "#f87171"
        chg_arrow = "▲" if day_chg_pct >= 0 else "▼"
        st.markdown(
            f'<div class="hero-panel">'
            f'  <div class="hero-meta">{symbol} · {exchange or "Listed Equity"}</div>'
            f'  <div class="ticker-name">{company_name}</div>'
            f'  <div class="ticker-meta">{sector} · {industry}</div>'
            f'  <div class="price-row">'
            f'    <span class="price-big">${current_price:,.2f}</span>'
            f'    <span class="price-chg" style="color:{chg_color}">{chg_arrow} {abs(day_chg_pct)*100:.2f}% today</span>'
            f'  </div>'
            f'  <div class="hero-note">Live market snapshot paired with historical multiple context and forward scenario work.</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    with hc3:
        trail_pe  = safe(info, "trailingPE")
        fwd_pe    = safe(info, "forwardPE")
        ps        = safe(info, "priceToSalesTrailing12Months")
        ev_ebitda = safe(info, "enterpriseToEbitda")
        st.markdown(
            f'<div class="hero-panel" style="height:100%">'
            f'  <div class="hero-meta">Quick Multiples</div>'
            f'  <div class="hero-stat-grid">'
            f'    <div class="hero-mini"><div class="hero-mini-label">Trailing P/E</div><div class="hero-mini-value">{f"{trail_pe:.1f}x" if trail_pe else "N/A"}</div></div>'
            f'    <div class="hero-mini"><div class="hero-mini-label">Forward P/E</div><div class="hero-mini-value">{f"{fwd_pe:.1f}x" if fwd_pe else "N/A"}</div></div>'
            f'    <div class="hero-mini"><div class="hero-mini-label">P/S</div><div class="hero-mini-value">{f"{ps:.1f}x" if ps else "N/A"}</div></div>'
            f'    <div class="hero-mini"><div class="hero-mini-label">EV/EBITDA</div><div class="hero-mini-value">{f"{ev_ebitda:.1f}x" if ev_ebitda else "N/A"}</div></div>'
            f'  </div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    # ── Analyst Target Bar ──
    target_low  = safe(info, "targetLowPrice")
    target_mean = safe(info, "targetMeanPrice")
    target_high = safe(info, "targetHighPrice")
    n_analysts  = safe(info, "numberOfAnalystOpinions")
    rec_key     = safe(info, "recommendationKey", "")

    if target_low and target_mean and target_high and target_low < target_high:
        bar_range = target_high - target_low

        # Clamp current price within the bar for display (it may be outside analyst range)
        cur_pct  = max(0.0, min(1.0, (current_price - target_low) / bar_range)) * 100
        mean_pct = max(0.0, min(1.0, (target_mean  - target_low) / bar_range)) * 100

        upside_to_mean = (target_mean / current_price - 1) * 100
        upside_color   = "#4ade80" if upside_to_mean >= 0 else "#f87171"
        upside_label   = f"{upside_to_mean:+.1f}% to avg target"

        rec_map = {
            "strong_buy":  ("Strong Buy",  "strong-buy"),
            "buy":         ("Buy",         "buy"),
            "hold":        ("Hold",        "hold"),
            "sell":        ("Sell",        "sell"),
            "strong_sell": ("Strong Sell", "strong-sell"),
        }
        rec_label, rec_cls = rec_map.get(rec_key.lower().replace(" ", "_"), (rec_key.title(), "hold"))
        analyst_count_txt = f"{int(n_analysts)} analysts" if n_analysts else ""

        st.markdown(
            f'<div class="at-shell">'
            f'  <div class="at-header">'
            f'    <span class="at-label">Analyst Targets</span>'
            f'    <span class="at-count">{analyst_count_txt}</span>'
            + (f'    <span class="at-rec {rec_cls}">{rec_label}</span>' if rec_label else "") +
            f'  </div>'
            f'  <div class="at-bar-track">'
            f'    <div class="at-bar-fill" style="left:{min(cur_pct,mean_pct):.1f}%;width:{abs(mean_pct-cur_pct):.1f}%"></div>'
            f'    <div class="at-mean-tick" style="left:{mean_pct:.1f}%"></div>'
            f'    <div class="at-dot-wrap" style="left:{cur_pct:.1f}%">'
            f'      <div class="at-tooltip">${current_price:,.2f}</div>'
            f'      <div class="at-dot" style="background:{"#4ade80" if upside_to_mean>=0 else "#f87171"}"></div>'
            f'    </div>'
            f'  </div>'
            f'  <div class="at-ticks">'
            f'    <div class="at-tick-group left"><div class="at-tick-price">${target_low:.0f}</div><div class="at-tick-label">Low</div></div>'
            f'    <div class="at-tick-group" style="left:{mean_pct:.1f}%"><div class="at-tick-price" style="color:#60a5fa">${target_mean:.0f}</div><div class="at-tick-label" style="color:#60a5fa">Avg</div></div>'
            f'    <div class="at-tick-group right"><div class="at-tick-price">${target_high:.0f}</div><div class="at-tick-label">High</div></div>'
            f'  </div>'
            f'  <div class="at-upside" style="color:{upside_color}">{upside_label}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    # ── EPS Estimates row ──
    eps_map = get_eps_estimates(data)
    now = datetime.now()
    cy_label  = f"CY{now.year}"
    ncy_label = f"CY{now.year + 1}"
    eps_cy  = eps_map.get(cy_label)
    eps_ncy = eps_map.get(ncy_label)

    e1, e1b, e2, e3 = st.columns(4)
    with e1:
        rev_growth = safe(info, "revenueGrowth")
        st.markdown(
            card("Revenue Growth (YoY)", fmt_pct(rev_growth),
                 sub_class="" if (rev_growth or 0) >= 0 else "down"),
            unsafe_allow_html=True,
        )
    with e1b:
        earn_growth = safe(info, "earningsGrowth")
        st.markdown(
            card("Earnings Growth (YoY)", fmt_pct(earn_growth),
                 sub_class="" if (earn_growth or 0) >= 0 else "down"),
            unsafe_allow_html=True,
        )
    with e2:
        cy_fwd_pe  = round(current_price / eps_cy,  1) if eps_cy and eps_cy > 0 else None
        ncy_fwd_pe = round(current_price / eps_ncy, 1) if eps_ncy and eps_ncy > 0 else None
        st.markdown(
            card(f"EPS Est. {cy_label}",
                 f"${eps_cy:.2f}" if eps_cy else "N/A",
                 f"{cy_fwd_pe}x fwd P/E" if cy_fwd_pe else None,
                 "neutral"),
            unsafe_allow_html=True,
        )
    with e3:
        st.markdown(
            card(f"EPS Est. {ncy_label}",
                 f"${eps_ncy:.2f}" if eps_ncy else "N/A",
                 f"{ncy_fwd_pe}x fwd P/E" if ncy_fwd_pe else None,
                 "neutral"),
            unsafe_allow_html=True,
        )

    # ── Claude: Valuation Method ──
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    client = anthropic.Anthropic(api_key=api_key) if api_key else None

    if not client:
        vm = None
        val_method = "PE"
    else:
        vm = get_cached_valuation_method(symbol)
        if vm is None:
            with st.spinner("Asking Claude…"):
                vm = claude_valuation_method(client, info)
            set_cached_valuation_method(symbol, vm)
        val_method = vm.get("primary", "PE")

    # ── Section 2: Where We Stand ──
    st.markdown('<div class="section-title">Where We Stand — Current Valuation</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-note">Read this first: where the current multiple sits versus its own history and whether expectations already look extended.</div>', unsafe_allow_html=True)

    pe_df = calc_pe_history(data)
    stats = pe_stats(pe_df)
    cur_pe = trail_pe

    eps_series = normalize_eps_series_to_market_basis(data, build_ttm_eps_series(data))
    if eps_series is not None and not eps_series.empty and current_price:
        latest_ttm_eps = eps_series.iloc[-1]
        if latest_ttm_eps and latest_ttm_eps > 0:
            cur_pe = round(current_price / latest_ttm_eps, 2)

    if pe_df is not None and not pe_df.empty and stats:
        # Chart
        st.plotly_chart(chart_pe_history(pe_df, stats, cur_pe), use_container_width=True, config={"displayModeBar": False})

        # Stats row
        s1, s2, s3, s4, s5 = st.columns(5)
        if cur_pe and stats["max"] != stats["min"]:
            pct = round((cur_pe - stats["min"]) / (stats["max"] - stats["min"]) * 100, 0)
        else:
            pct = 50
        pe_color = "down" if pct > 75 else "" if pct > 40 else "neutral"
        vs_avg = ((cur_pe / stats["avg"]) - 1) * 100 if cur_pe and stats.get("avg") else None

        with s1:
            sub = f"{fmt_pct(vs_avg/100)} vs avg" if vs_avg is not None else ""
            sub_cls = "down" if vs_avg and vs_avg > 10 else "" if vs_avg and vs_avg < -10 else "neutral"
            st.markdown(card("Current P/E", f"{cur_pe:.1f}x" if cur_pe else "N/A", sub, sub_cls), unsafe_allow_html=True)
        with s2:
            st.markdown(card("3yr Low",  f"{stats['min']}x"), unsafe_allow_html=True)
        with s3:
            st.markdown(card("3yr High", f"{stats['max']}x"), unsafe_allow_html=True)
        with s4:
            st.markdown(card("3yr Avg",  f"{stats['avg']}x"), unsafe_allow_html=True)
        with s5:
            st.markdown(card("Percentile", f"{pct:.0f}th",
                             "overvalued vs history" if pct > 70 else "undervalued vs history" if pct < 30 else "fair range",
                             "down" if pct > 70 else "" if pct < 30 else "neutral"),
                        unsafe_allow_html=True)

        # Gauge bar
        pct_clamped = max(0, min(100, pct))
        bar_color = "#f87171" if pct_clamped > 70 else "#fbbf24" if pct_clamped > 40 else "#4ade80"
        st.markdown(
            f'<div class="pe-bar-container">'
            f'  <div style="display:flex;justify-content:space-between;margin-bottom:4px;font-size:0.75rem;color:#6b7db3">'
            f'    <span>Low {stats["min"]}x</span><span>Avg {stats["avg"]}x</span><span>High {stats["max"]}x</span>'
            f'  </div>'
            f'  <div class="pe-bar-track">'
            f'    <div class="pe-bar-fill" style="width:{pct_clamped}%;background:{bar_color}40"></div>'
            f'    <div class="pe-bar-dot" style="left:{pct_clamped}%;background:{bar_color}"></div>'
            f'  </div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    else:
        st.info("Historical PE data unavailable — insufficient quarterly earnings history.")
        if cur_pe:
            st.markdown(card("Current P/E", f"{cur_pe:.1f}x"), unsafe_allow_html=True)

    if client and cur_pe:
        st.markdown('<div class="section-title">P/E Expectations</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-note">This asks Claude what the current multiple already assumes, and what kind of guidance or business evidence would expand or compress that multiple.</div>', unsafe_allow_html=True)

        if "pe_expectations" not in st.session_state or st.session_state.get("pe_symbol") != symbol:
            pe_expectations = get_cached_pe_expectations(symbol)
            if pe_expectations is None:
                with st.spinner("Claude is mapping what this P/E already prices in…"):
                    pe_expectations = claude_pe_expectations(
                        client,
                        info,
                        stats,
                        cur_pe,
                        current_price,
                        eps_ncy or safe(info, "forwardEps"),
                        pe_df,
                    )
                set_cached_pe_expectations(symbol, pe_expectations)
            st.session_state["pe_expectations"] = pe_expectations
            st.session_state["pe_symbol"] = symbol

        render_pe_expectations(st.session_state["pe_expectations"])

    # ── Section 3: Growth Potential ──
    st.markdown('<div class="section-title">Growth Potential — Price Targets</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-note">Forward scenarios should compress to three quick outcomes: bear, base, and bull. The chart is primary; the cards are just the fast read.</div>', unsafe_allow_html=True)

    # Use analyst EPS estimates (already computed above)
    trail_eps = eps_cy   # CY2026 analyst consensus
    fwd_eps   = eps_ncy  # CY2027 analyst consensus

    cy  = cy_label
    ncy = ncy_label

    if trail_eps and fwd_eps and stats:
        scen_cy, scen_ncy = compute_targets(trail_eps, fwd_eps, stats, current_price)
        if scen_cy and scen_ncy:
            st.plotly_chart(
                chart_price_targets(current_price, scen_cy, scen_ncy, cy, ncy, "P/E"),
                use_container_width=True,
                config={"displayModeBar": False},
            )
            # Summary cards below chart
            cases = ["Bear", "Base", "Bull"]
            card_colors = ["#f97316", "#60a5fa", "#34d399"]
            cols = st.columns(3)
            for i, (s_cy, s_ncy, col, case, color) in enumerate(zip(scen_cy, scen_ncy, cols, cases, card_colors)):
                with col:
                    upside_cy  = s_cy["upside"]
                    upside_ncy = s_ncy["upside"]
                    u_cls_cy   = "down" if upside_cy < 0 else ""
                    u_cls_ncy  = "down" if upside_ncy < 0 else ""
                    st.markdown(
                        f'<div class="target-card" style="border-top:3px solid {color}">'
                        f'  <div class="target-case" style="color:{color}">{case} ({s_cy["pe"]:.0f}x PE)</div>'
                        f'  <div style="display:flex;justify-content:space-around;margin-top:8px">'
                        f'    <div>'
                        f'      <div class="target-label">{cy}</div>'
                        f'      <div class="target-price">${s_cy["price"]:.0f}</div>'
                        f'      <div class="target-upside" style="color:{"#f87171" if upside_cy < 0 else "#4ade80"}">{upside_cy:+.1f}%</div>'
                        f'    </div>'
                        f'    <div style="width:1px;background:#1f2a45"></div>'
                        f'    <div>'
                        f'      <div class="target-label">{ncy}</div>'
                        f'      <div class="target-price">${s_ncy["price"]:.0f}</div>'
                        f'      <div class="target-upside" style="color:{"#f87171" if upside_ncy < 0 else "#4ade80"}">{upside_ncy:+.1f}%</div>'
                        f'    </div>'
                        f'  </div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
        else:
            st.info("Insufficient data to compute P/E based price targets.")
    else:
        st.info("Insufficient data to compute P/E based price targets.")

    # ── Section 5: AI Interpretation ──
    st.markdown('<div class="section-title">AI Interpretation</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-note">Use this after the numbers. It should help frame the lens and the catalysts, not replace the valuation work above.</div>', unsafe_allow_html=True)

    if not client:
        st.warning("Set `ANTHROPIC_API_KEY` env variable to enable AI features.")
    else:
        col_a, col_b = st.columns([3, 2])
        with col_a:
            st.markdown(
                f'<div class="ai-block">'
                f'  <div class="ai-badge">Primary Lens</div>'
                f'  <div class="ai-method-name">{vm.get("primary","PE")}</div>'
                f'  <div class="ai-reason">{vm.get("primary_reason","")}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
        with col_b:
            secondary_name = vm.get("secondary") or "None"
            secondary_reason = vm.get("secondary_reason") or "No secondary method surfaced above the primary lens."
            st.markdown(
                f'<div class="ai-block">'
                f'  <div class="ai-badge">Secondary Watch</div>'
                f'  <div class="ai-method-name">{secondary_name}</div>'
                f'  <div class="ai-reason">{secondary_reason}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

        st.markdown('<div class="section-title">Catalyst Tracker</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-note">Catalysts are split by upside and downside so expectation gaps are easier to scan than a mixed feed.</div>', unsafe_allow_html=True)

        if "growth_story" not in st.session_state or st.session_state.get("gs_symbol") != symbol:
            story = get_cached_growth_story(symbol)
            if story is None:
                with st.spinner("Claude is analyzing growth story…"):
                    story = claude_growth_story(client, info, stats, cur_pe or 0)
                set_cached_growth_story(symbol, story)
            st.session_state["growth_story"] = story
            st.session_state["gs_symbol"] = symbol

        story_text = st.session_state["growth_story"]
        render_growth_story(story_text)

        if st.button("↺ Regenerate Analysis"):
            invalidate_cached_growth_story(symbol)
            invalidate_cached_valuation_method(symbol)
            invalidate_cached_pe_expectations(symbol)
            del st.session_state["growth_story"]
            if "pe_expectations" in st.session_state:
                del st.session_state["pe_expectations"]
            st.rerun()

    # ── Footer ──
    st.markdown(
        '<div style="border-top:1px solid #1f2a45;margin-top:40px;padding-top:12px;'
        'color:#4a5577;font-size:0.75rem">Data via yfinance · AI via Claude · For informational purposes only. '
        'Not financial advice.</div>',
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
