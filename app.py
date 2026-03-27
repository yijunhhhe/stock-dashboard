"""
Stock Intelligence Dashboard
AI-powered valuation analysis using yfinance + Claude
"""

import os
import warnings
from datetime import datetime

import anthropic
import streamlit as st
from dotenv import load_dotenv

from styles import CSS
from utils import safe, fmt_pct
from data_fetching import (
    fetch_data,
    get_eps_estimates,
    build_ttm_eps_series,
    normalize_eps_series_to_market_basis,
    calc_pe_history,
    pe_stats,
)
from cache import (
    get_cached_valuation_method,
    set_cached_valuation_method,
    invalidate_cached_valuation_method,
    get_cached_pe_expectations,
    set_cached_pe_expectations,
    invalidate_cached_pe_expectations,
    get_cached_growth_story,
    set_cached_growth_story,
    invalidate_cached_growth_story,
)
from ai_engine import (
    claude_valuation_method,
    claude_growth_story,
    claude_pe_expectations,
    render_pe_expectations,
    render_growth_story,
)
from charts import chart_pe_history, chart_price_targets, compute_targets

load_dotenv(".env.local")
warnings.filterwarnings("ignore")

# ─── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Stock Intelligence",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(CSS, unsafe_allow_html=True)


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
        st.error(
            f"No price data found for **{symbol}**. "
            "This can happen when Yahoo Finance rate-limits requests from cloud servers. "
            "Wait 30 seconds and try again, or verify the ticker is correct."
        )
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
        st.plotly_chart(chart_pe_history(pe_df, stats, cur_pe), use_container_width=True, config={"displayModeBar": False})

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

    trail_eps = eps_cy
    fwd_eps   = eps_ncy
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
            cases = ["Bear", "Base", "Bull"]
            card_colors = ["#f97316", "#60a5fa", "#34d399"]
            cols = st.columns(3)
            for i, (s_cy, s_ncy, col, case, color) in enumerate(zip(scen_cy, scen_ncy, cols, cases, card_colors)):
                with col:
                    upside_cy  = s_cy["upside"]
                    upside_ncy = s_ncy["upside"]
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


main()
