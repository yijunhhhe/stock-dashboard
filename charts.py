import plotly.graph_objects as go


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
