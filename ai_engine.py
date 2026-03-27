import json
import re
import streamlit as st

from utils import safe, fmt_num, fmt_pct


# ── Claude API Calls ──────────────────────────────────────────────────────────

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


# ── JSON Parsing ──────────────────────────────────────────────────────────────

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


# ── Rendering ─────────────────────────────────────────────────────────────────

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
