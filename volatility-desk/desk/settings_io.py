"""Settings read/write - JSON file or env override."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional


def load_settings(path: Optional[Path] = None) -> Dict[str, Any]:
    """Load settings from JSON file (or env var override)."""
    if path is None:
        # Check env var for override
        env_path = os.environ.get("VOLATILITY_DESK_SETTINGS")
        if env_path:
            path = Path(env_path)
        else:
            # Default to data/sample_settings.json
            path = Path(__file__).parent.parent / "data" / "sample_settings.json"
    
    if not path.is_file():
        return _default_settings()
    
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else _default_settings()
    except Exception:
        return _default_settings()


def save_settings(updates: Dict[str, Any], path: Optional[Path] = None) -> None:
    """Merge updates into existing settings and save."""
    if path is None:
        env_path = os.environ.get("VOLATILITY_DESK_SETTINGS")
        if env_path:
            path = Path(env_path)
        else:
            path = Path(__file__).parent.parent / "data" / "sample_settings.json"
    
    # Load existing
    existing = load_settings(path)
    
    # Merge (shallow update for top-level keys)
    existing.update(updates)
    
    # Write back
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(existing, f, indent=2)


def _default_settings() -> Dict[str, Any]:
    """Return default settings when file not found."""
    return {
        "runner_enabled": False,
        "allow_long": True,
        "allow_short": True,
        "universe": ["SMCI", "SOFI", "RDW"],
        "algos": {
            "GEX_STRATEGY": {"enabled": True, "label": "GEX Stock", "tickers": ["RDW"]},
            "VWAP_STRATEGY": {"enabled": True, "label": "VWAP MultiDay", "tickers": ["SMCI"]},
            "IWM_STRATEGY": {"enabled": False, "label": "IWM Calendar", "tickers": ["IWM"]},
            "WISH_STRATEGY": {"enabled": False, "label": "WISH QQQ Call", "tickers": ["QQQ"]},
            "RSI_STRATEGY": {"enabled": False, "label": "Index RSI MR", "tickers": ["SPY", "QQQ", "IWM"]},
            "TV_STRATEGY": {"enabled": False, "label": "TradingView Alerts", "tickers": []}
        },
        "poll_sec": 60
    }


def get_signal_path() -> Path:
    """Return signal log path (env override or default)."""
    env_path = os.environ.get("VOLATILITY_DESK_SIGNALS")
    if env_path:
        return Path(env_path)
    else:
        return Path(__file__).parent.parent / "data" / "sample_signals.jsonl"
