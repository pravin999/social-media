"""Core analytics: FIFO trade matching, KPI aggregation, cross-tabs."""

from __future__ import annotations

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# Module-level cache for mtime-keyed snapshots
_CACHE: Dict[str, Any] = {"key": None, "snap": None, "at": 0.0}


def _setup_label(algo_id: Any) -> str:
    """Extract setup label from algo_id (e.g., GEX_STRATEGY -> GEX)."""
    a = str(algo_id or "").upper()
    for prefix in ["GEX", "VWAP", "IWM", "WISH", "RSI", "TV"]:
        if prefix in a:
            return prefix
    return (a or "OTHER")[:10]


def _mtime(path: Path) -> float:
    """Get file modification time, 0 if not found."""
    try:
        return path.stat().st_mtime if path.is_file() else 0.0
    except OSError:
        return 0.0


def load_signals(path: Path, limit: int = 1000) -> List[Dict[str, Any]]:
    """Load signal events from JSONL file, return most recent N in chronological order."""
    if not path.is_file():
        return []
    
    events: List[Dict[str, Any]] = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        
        # Sort by timestamp descending to get most recent, take last N
        events.sort(key=lambda e: float(e.get("ts") or 0), reverse=True)
        recent = events[:limit]
        
        # Reverse to chronological order (oldest first) for FIFO matching
        recent.reverse()
        return recent
    except Exception:
        return []


def compute_snapshot(
    events: List[Dict[str, Any]], 
    *, 
    today_tz: Optional[Any] = None
) -> Dict[str, Any]:
    """
    Compute closed-trade analytics using FIFO matching.
    
    Args:
        events: Signal events in chronological order (oldest first)
    
    Returns:
        total_pnl, today_pnl, win_rate, trade_count, equity_curve,
        by_setup, by_ticker, by_day, by_setup_ticker (cross-tab), open_positions
    """
    # Try to get ET timezone for today calculation
    try:
        import zoneinfo
        et = zoneinfo.ZoneInfo("America/New_York")
        today = datetime.now(tz=et).date()
    except Exception:
        et = None
        today = None
    
    # Events should be in chronological order (oldest first)
    
    # FIFO matching
    opens: Dict[str, List[Dict[str, Any]]] = {}
    closed_trades: List[Dict[str, Any]] = []
    equity: List[float] = []
    running_pnl = 0.0
    today_pnl = 0.0
    
    for ev in events:
        if not ev.get("ok"):
            continue
        
        action = str(ev.get("action") or "").lower()
        sym = str(ev.get("symbol") or "").upper()
        if not sym or action not in ("entry", "exit"):
            continue
        
        try:
            px = float(ev.get("price"))
            qty = float(ev.get("qty") or 0)
            ts = float(ev.get("ts") or 0)
        except (TypeError, ValueError):
            continue
        
        if px <= 0 or qty <= 0:
            continue
        
        if action == "entry":
            opens.setdefault(sym, []).append(ev)
            continue
        
        # Exit: match with oldest entry
        stack = opens.get(sym) or []
        if not stack:
            continue
        
        ent = stack.pop(0)
        try:
            ep = float(ent.get("price"))
            eqty = float(ent.get("qty") or qty)
            ets = float(ent.get("ts") or ts)
        except (TypeError, ValueError):
            continue
        
        if ep <= 0:
            continue
        
        q = min(eqty, qty)
        eside = str(ent.get("side") or "buy").lower()
        
        # Calculate PnL
        if eside == "buy":
            pnl = (px - ep) * q
        else:
            pnl = (ep - px) * q
        
        running_pnl += pnl
        equity.append(running_pnl)
        
        setup = _setup_label(ent.get("algo_id"))
        
        closed_trades.append({
            "symbol": sym,
            "setup": setup,
            "side": eside,
            "entry_px": ep,
            "exit_px": px,
            "qty": q,
            "pnl": pnl,
            "entry_ts": ets,
            "exit_ts": ts,
            "hold_sec": ts - ets
        })
        
        # Today PnL
        if et is not None and today is not None and ts:
            try:
                exit_date = datetime.fromtimestamp(ts, tz=et).date()
                if exit_date == today:
                    today_pnl += pnl
            except Exception:
                pass
    
    # Aggregate stats
    n = len(closed_trades)
    wins = sum(1 for t in closed_trades if t["pnl"] > 0)
    win_rate = (100.0 * wins / n) if n else None
    
    # By setup
    by_setup: Dict[str, Dict[str, Any]] = {}
    for t in closed_trades:
        setup = t["setup"]
        if setup not in by_setup:
            by_setup[setup] = {"pnl": 0.0, "n": 0, "wins": 0, "hold_sec": 0.0}
        by_setup[setup]["pnl"] += t["pnl"]
        by_setup[setup]["n"] += 1
        by_setup[setup]["hold_sec"] += t["hold_sec"]
        if t["pnl"] > 0:
            by_setup[setup]["wins"] += 1
    
    # By ticker
    by_ticker: Dict[str, Dict[str, Any]] = {}
    for t in closed_trades:
        sym = t["symbol"]
        if sym not in by_ticker:
            by_ticker[sym] = {"pnl": 0.0, "n": 0, "wins": 0, "hold_sec": 0.0}
        by_ticker[sym]["pnl"] += t["pnl"]
        by_ticker[sym]["n"] += 1
        by_ticker[sym]["hold_sec"] += t["hold_sec"]
        if t["pnl"] > 0:
            by_ticker[sym]["wins"] += 1
    
    # By day
    by_day: Dict[str, float] = {}
    if et is not None:
        for t in closed_trades:
            try:
                d = datetime.fromtimestamp(t["exit_ts"], tz=et).date()
                by_day[d.isoformat()] = by_day.get(d.isoformat(), 0.0) + t["pnl"]
            except Exception:
                pass
    
    # Cross-tab: setup × ticker
    by_setup_ticker: Dict[str, Dict[str, float]] = {}
    for t in closed_trades:
        setup = t["setup"]
        sym = t["symbol"]
        if setup not in by_setup_ticker:
            by_setup_ticker[setup] = {}
        by_setup_ticker[setup][sym] = by_setup_ticker[setup].get(sym, 0.0) + t["pnl"]
    
    # Open positions (unmatched entries)
    open_positions: List[Dict[str, Any]] = []
    for sym, stack in opens.items():
        for ent in stack:
            open_positions.append({
                "symbol": sym,
                "setup": _setup_label(ent.get("algo_id")),
                "side": str(ent.get("side") or "buy").lower(),
                "entry_px": float(ent.get("price")),
                "qty": float(ent.get("qty") or 0),
                "ts": float(ent.get("ts") or 0)
            })
    
    # Downsample equity curve to max 100 points
    if len(equity) > 100:
        step = (len(equity) - 1) / 99.0
        equity = [equity[int(i * step)] for i in range(100)]
    
    return {
        "total_pnl": running_pnl,
        "today_pnl": today_pnl,
        "win_rate": win_rate,
        "n": n,
        "wins": wins,
        "equity": equity,
        "by_setup": by_setup,
        "by_ticker": by_ticker,
        "by_day": by_day,
        "by_setup_ticker": by_setup_ticker,
        "open_positions": open_positions,
        "closed_trades": closed_trades
    }


def cached_snapshot(
    signal_path: Path,
    *,
    cache_ttl_sec: float = 2.0
) -> Dict[str, Any]:
    """
    Return cached snapshot if mtime unchanged and TTL not expired.
    This avoids re-parsing JSONL on every fragment click.
    """
    key = _mtime(signal_path)
    now = time.monotonic()
    
    cached = _CACHE.get("snap")
    if cached and _CACHE.get("key") == key:
        return cached
    
    # Also allow stale cache if TTL not expired
    if cached and (now - float(_CACHE.get("at") or 0)) < cache_ttl_sec:
        return cached
    
    # Recompute
    events = load_signals(signal_path)
    snap = compute_snapshot(events)
    
    _CACHE["key"] = key
    _CACHE["at"] = now
    _CACHE["snap"] = snap
    
    return snap
