CSS = """
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
"""
