"""Sample signal event generator for demo mode."""

from __future__ import annotations

import json
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List


def _setup_label(i: int) -> str:
    """Return setup name by index for variety."""
    setups = ["GEX", "VWAP", "IWM", "WISH", "RSI", "TV"]
    return setups[i % len(setups)]


def generate_sample_signals(count: int = 200, days_back: int = 30) -> List[Dict[str, Any]]:
    """Generate realistic sample signal events with entries and exits."""
    tickers = ["SMCI", "SOFI", "RDW", "PLTR", "NVDA", "AMD", "TSLA", "AAPL", "SPY", "QQQ"]
    events: List[Dict[str, Any]] = []
    now = datetime.now()
    
    # Base prices for tickers
    base_prices = {
        "SMCI": 25.0, "SOFI": 12.0, "RDW": 8.0, "PLTR": 35.0, 
        "NVDA": 450.0, "AMD": 120.0, "TSLA": 240.0, "AAPL": 180.0,
        "SPY": 480.0, "QQQ": 420.0
    }
    
    for i in range(count):
        # Random timestamp within last N days
        ts_offset = random.uniform(0, days_back * 86400)
        ts = (now - timedelta(seconds=ts_offset)).timestamp()
        
        ticker = random.choice(tickers)
        base_px = base_prices[ticker]
        
        # Entry event
        setup_idx = random.randint(0, 5)
        algo_id = _setup_label(setup_idx)
        side = random.choice(["buy", "sell"])
        entry_px = base_px * random.uniform(0.95, 1.05)
        qty = random.randint(1, 10)
        
        events.append({
            "ts": ts,
            "symbol": ticker,
            "action": "entry",
            "side": side,
            "price": round(entry_px, 2),
            "qty": qty,
            "algo_id": f"{algo_id}_STRATEGY",
            "ok": True,
            "reason": f"{algo_id} signal triggered",
            "broker": random.choice(["webull", "robinhood", "oanda"])
        })
        
        # 85% of entries get matched exits
        if random.random() < 0.85:
            # Exit 30s to 2 hours later
            exit_ts = ts + random.uniform(30, 7200)
            
            # Winners: 55%, losers: 35%, breakeven: 10%
            outcome = random.choices(["win", "loss", "be"], weights=[55, 35, 10])[0]
            
            if outcome == "win":
                exit_px = entry_px * random.uniform(1.01, 1.08) if side == "buy" else entry_px * random.uniform(0.92, 0.99)
            elif outcome == "loss":
                exit_px = entry_px * random.uniform(0.92, 0.99) if side == "buy" else entry_px * random.uniform(1.01, 1.08)
            else:
                exit_px = entry_px * random.uniform(0.998, 1.002)
            
            events.append({
                "ts": exit_ts,
                "symbol": ticker,
                "action": "exit",
                "side": "sell" if side == "buy" else "buy",
                "price": round(exit_px, 2),
                "qty": qty,
                "algo_id": f"{algo_id}_STRATEGY",
                "ok": True,
                "reason": "exit signal" if outcome == "win" else ("stop loss" if outcome == "loss" else "time exit"),
                "broker": events[-1]["broker"]
            })
    
    # Sort by timestamp
    events.sort(key=lambda e: e["ts"])
    
    return events


def write_sample_jsonl(path: Path, count: int = 200, days_back: int = 30) -> None:
    """Write sample signals to JSONL file."""
    events = generate_sample_signals(count, days_back)
    with open(path, "w", encoding="utf-8") as f:
        for event in events:
            f.write(json.dumps(event) + "\n")


def write_sample_settings(path: Path) -> None:
    """Write sample settings JSON."""
    settings = {
        "runner_enabled": True,
        "allow_long": True,
        "allow_short": True,
        "universe": ["SMCI", "SOFI", "RDW", "PLTR", "NVDA", "AMD"],
        "algos": {
            "GEX_STRATEGY": {
                "enabled": True,
                "label": "GEX Stock",
                "fund_pct": 50.0,
                "min_conf": 10.0,
                "max_hold_days": 5,
                "tickers": ["RDW", "SOFI"]
            },
            "VWAP_STRATEGY": {
                "enabled": True,
                "label": "VWAP MultiDay",
                "max_notional": 100.0,
                "tickers": ["SMCI", "NVDA"]
            },
            "IWM_STRATEGY": {
                "enabled": True,
                "label": "IWM Calendar",
                "contracts": 1,
                "tickers": ["IWM"]
            },
            "WISH_STRATEGY": {
                "enabled": False,
                "label": "WISH QQQ Call",
                "tickers": ["QQQ"]
            },
            "RSI_STRATEGY": {
                "enabled": True,
                "label": "Index RSI MR",
                "shares": 2,
                "tickers": ["SPY", "QQQ", "IWM"]
            },
            "TV_STRATEGY": {
                "enabled": False,
                "label": "TradingView Alerts",
                "tickers": []
            }
        },
        "poll_sec": 60
    }
    
    with open(path, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2)


if __name__ == "__main__":
    # Generate sample data for testing
    data_dir = Path(__file__).parent.parent / "data"
    data_dir.mkdir(exist_ok=True)
    
    write_sample_jsonl(data_dir / "sample_signals.jsonl", count=250, days_back=30)
    write_sample_settings(data_dir / "sample_settings.json")
    
    print(f"Generated sample data in {data_dir}")
