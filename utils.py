import numpy as np


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
