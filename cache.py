import json
from datetime import datetime
from pathlib import Path

CACHE_PATH = Path(".cache/growth_story_cache.json")
CACHE_TTL_HOURS = 24
CACHE_MAX_ENTRIES = 100


def _load():
    if not CACHE_PATH.exists():
        return {}
    try:
        with CACHE_PATH.open("r", encoding="utf-8") as f:
            payload = json.load(f)
        return payload if isinstance(payload, dict) else {}
    except Exception:
        return {}


def _save(cache):
    try:
        CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        with CACHE_PATH.open("w", encoding="utf-8") as f:
            json.dump(cache, f)
    except Exception:
        pass


def _prune(cache):
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
        if age_hours <= CACHE_TTL_HOURS:
            pruned[key] = entry

    if len(pruned) <= CACHE_MAX_ENTRIES:
        return pruned

    ranked = sorted(
        pruned.items(),
        key=lambda item: item[1].get("last_accessed_at", item[1].get("fetched_at", "")),
        reverse=True,
    )
    return dict(ranked[:CACHE_MAX_ENTRIES])


# ── Growth Story ──────────────────────────────────────────────────────────────

def _key_growth_story(symbol):
    return f"v2:{symbol.upper().strip()}"


def get_cached_growth_story(symbol):
    cache = _prune(_load())
    key = _key_growth_story(symbol)
    entry = cache.get(key)
    if not entry:
        _save(cache)
        return None
    entry["last_accessed_at"] = datetime.utcnow().isoformat()
    cache[key] = entry
    _save(cache)
    return entry.get("story")


def set_cached_growth_story(symbol, story):
    cache = _prune(_load())
    now = datetime.utcnow().isoformat()
    cache[_key_growth_story(symbol)] = {"story": story, "fetched_at": now, "last_accessed_at": now}
    _save(_prune(cache))


def invalidate_cached_growth_story(symbol):
    cache = _load()
    key = _key_growth_story(symbol)
    if key in cache:
        del cache[key]
        _save(_prune(cache))


# ── Valuation Method ──────────────────────────────────────────────────────────

def _key_valuation_method(symbol):
    return f"valmethod:v1:{symbol.upper().strip()}"


def get_cached_valuation_method(symbol):
    cache = _prune(_load())
    key = _key_valuation_method(symbol)
    entry = cache.get(key)
    if not entry:
        _save(cache)
        return None
    entry["last_accessed_at"] = datetime.utcnow().isoformat()
    cache[key] = entry
    _save(cache)
    return entry.get("value")


def set_cached_valuation_method(symbol, value):
    cache = _prune(_load())
    now = datetime.utcnow().isoformat()
    cache[_key_valuation_method(symbol)] = {"value": value, "fetched_at": now, "last_accessed_at": now}
    _save(_prune(cache))


def invalidate_cached_valuation_method(symbol):
    cache = _load()
    key = _key_valuation_method(symbol)
    if key in cache:
        del cache[key]
        _save(_prune(cache))


# ── P/E Expectations ──────────────────────────────────────────────────────────

def _key_pe_expectations(symbol):
    return f"peexpect:v3:{symbol.upper().strip()}"


def get_cached_pe_expectations(symbol):
    cache = _prune(_load())
    key = _key_pe_expectations(symbol)
    entry = cache.get(key)
    if not entry:
        _save(cache)
        return None
    entry["last_accessed_at"] = datetime.utcnow().isoformat()
    cache[key] = entry
    _save(cache)
    return entry.get("value")


def set_cached_pe_expectations(symbol, value):
    cache = _prune(_load())
    now = datetime.utcnow().isoformat()
    cache[_key_pe_expectations(symbol)] = {"value": value, "fetched_at": now, "last_accessed_at": now}
    _save(_prune(cache))


def invalidate_cached_pe_expectations(symbol):
    cache = _load()
    key = _key_pe_expectations(symbol)
    if key in cache:
        del cache[key]
        _save(_prune(cache))


# ── Forward Metrics ───────────────────────────────────────────────────────────

def _key_forward_metrics(symbol):
    return f"forwardmetrics:v4:{symbol.upper().strip()}"


def get_cached_forward_metrics(symbol):
    cache = _prune(_load())
    key = _key_forward_metrics(symbol)
    entry = cache.get(key)
    if not entry:
        _save(cache)
        return None
    entry["last_accessed_at"] = datetime.utcnow().isoformat()
    cache[key] = entry
    _save(cache)
    return entry.get("value")


def set_cached_forward_metrics(symbol, value):
    cache = _prune(_load())
    now = datetime.utcnow().isoformat()
    cache[_key_forward_metrics(symbol)] = {"value": value, "fetched_at": now, "last_accessed_at": now}
    _save(_prune(cache))


def invalidate_cached_forward_metrics(symbol):
    cache = _load()
    key = _key_forward_metrics(symbol)
    if key in cache:
        del cache[key]
        _save(_prune(cache))


def clear_all_caches():
    try:
        if CACHE_PATH.exists():
            CACHE_PATH.unlink()
    except Exception:
        _save({})
