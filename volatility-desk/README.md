# Volatility Desk ⚡

A blazing-fast, self-contained Streamlit trading performance desk for algo trading operations.

## Features

- **< 200ms first paint** with module-level mtime caching
- **SVG charts by default** — no Plotly/matplotlib import on hot path
- **Fragment-based navigation** — chart/tab clicks stay local, no full app rerun
- **Five integrated views:**
  - **Overall** — hero PnL, KPIs, open positions, equity curve
  - **Setups** — ranked by PnL with drill-down to ticker breakdown
  - **Tickers** — ranked by PnL with drill-down to setup breakdown
  - **Cross** — setup × ticker matrix heatmap
  - **Config** — strategy toggles, ticker lists, sizing knobs
- **Demo mode included** — sample signal generator runs out of the box
- **Dark neon aesthetic** — green/cyan/magenta, sharp and uncluttered

## Quick Start

```bash
cd volatility-desk
pip install -r requirements.txt
streamlit run app.py
```

The app starts with **sample data** (250 trades over 30 days). The UI loads instantly and all views work offline.

## Project Structure

```
volatility-desk/
  app.py                  # Main Streamlit entry point
  requirements.txt
  README.md
  desk/
    snap.py               # Core analytics: FIFO matching, KPI aggregation
    charts_svg.py         # SVG equity curve, bars, heatmap (no Plotly)
    views.py              # Overall | Setups | Tickers | Cross | Config
    settings_io.py        # JSON settings read/write
    sample_data.py        # Demo signal generator
  data/
    sample_signals.jsonl  # Generated sample signals
    sample_settings.json  # Generated sample settings
  tests/
    test_snap.py          # Unit tests for FIFO matching, aggregates
```

## Data Model

### Signal Event (JSONL)

```json
{
  "ts": 1695000000.0,
  "symbol": "SMCI",
  "action": "entry",
  "side": "buy",
  "price": 25.5,
  "qty": 5,
  "algo_id": "VWAP_STRATEGY",
  "ok": true,
  "reason": "VWAP signal triggered",
  "broker": "webull"
}
```

- **action**: `entry` or `exit`
- **side**: `buy` or `sell`
- **algo_id**: setup identifier (GEX_STRATEGY, VWAP_STRATEGY, IWM_STRATEGY, etc.)
- **ok**: `true` for successful executions (only `ok=true` events are matched)

### Settings (JSON)

```json
{
  "runner_enabled": true,
  "allow_long": true,
  "allow_short": true,
  "algos": {
    "GEX_STRATEGY": {
      "enabled": true,
      "label": "GEX Stock",
      "fund_pct": 50.0,
      "min_conf": 10.0,
      "max_hold_days": 5,
      "tickers": ["RDW", "SOFI"]
    },
    "VWAP_STRATEGY": {
      "enabled": true,
      "label": "VWAP MultiDay",
      "max_notional": 100.0,
      "tickers": ["SMCI", "NVDA"]
    }
  }
}
```

## Using Real Data

Point the app at your own signal log and settings:

```bash
export VOLATILITY_DESK_SIGNALS=/path/to/your/signals.jsonl
export VOLATILITY_DESK_SETTINGS=/path/to/your/settings.json
streamlit run app.py
```

The app automatically picks up these paths. The signal log format is simple JSONL with the fields above.

## Views Explained

### Overall

- **Hero PnL**: total, today, win rate, trade count
- **Open positions**: chips showing current holdings (setup, symbol, side)
- **Chart pills**: Curve / By setup / By ticker / By day
  - All rendered as inline SVG for instant display

### Setups

- **Ranked table**: PnL, trades, win%, avg hold time per setup
- **Bar chart**: top 8 setups by |PnL|
- **Drill-down**: select a setup to see ticker breakdown

### Tickers

- **Ranked table**: PnL, trades, win%, avg hold time per ticker
- **Bar chart**: top 10 tickers by |PnL|
- **Drill-down**: select a ticker to see setup breakdown

### Cross

- **Heatmap**: setup (rows) × ticker (cols), cell color = PnL intensity
- **Detail panel**: select setup + ticker for exact PnL

### Config

- **Global toggles**: Accept entries, Allow long/short
- **Per-strategy config**: enable/disable, ticker CSV, sizing params
  - GEX: fund %, min conf %, max hold days
  - VWAP: max notional
  - IWM/WISH: contracts
  - RSI: shares
- **Save**: writes back to `settings.json`
- **Status**: DEMO / LIVE indicator (stub in v1)

## Analytics Details

### FIFO Matching

Closed trades are computed by matching `exit` events to the oldest `entry` for the same symbol:

- Entry side `buy` + Exit side `sell` → long trade
- Entry side `sell` + Exit side `buy` → short trade
- PnL = `(exit_px - entry_px) * qty` for longs, `(entry_px - exit_px) * qty` for shorts

### Setup Labeling

Setup names are extracted from `algo_id` by prefix matching:

- `GEX_STRATEGY` → **GEX**
- `VWAP_STRATEGY` → **VWAP**
- `IWM_STRATEGY` → **IWM**
- `WISH_STRATEGY` → **WISH**
- `RSI_STRATEGY` → **RSI**
- `TV_STRATEGY` → **TV**
- Unknown → **OTHER**

### Aggregations

- **by_setup**: PnL, trade count, wins, avg hold time per setup
- **by_ticker**: PnL, trade count, wins, avg hold time per ticker
- **by_day**: total PnL per calendar day (ET timezone)
- **by_setup_ticker**: cross-tab matrix for heatmap

### Equity Curve

- Running PnL after each closed trade
- Downsampled to max 100 points for SVG rendering

## Performance Goals (Non-Negotiable)

- ✅ **First paint < 200ms** — achieved via mtime cache, no pandas/plotly on hot path
- ✅ **Fragment-local clicks** — chart pills and tab switches do not rerun entire app
- ✅ **SVG by default** — Plotly only if explicitly added behind an expander
- ✅ **Equity curve downsampled** — max 100 points for instant rendering
- ✅ **Demo mode works offline** — no broker dependencies

## Testing

```bash
pytest tests/
```

Tests cover:
- FIFO matching logic
- Setup label extraction
- By-setup / by-ticker aggregates
- Cross-tab matrix construction

## Roadmap (Future)

- [ ] Live data polling (optional refresh every N seconds)
- [ ] Export to CSV
- [ ] Plotly charts behind "Advanced charts" expander
- [ ] Real broker integration hooks (WebSocket listeners)
- [ ] Configurable timezone (default ET)
- [ ] Trade detail modal (entry/exit timestamps, hold time, PnL%)

## Design Philosophy

This app is a **clean rewrite** inspired by two prior desks (neon_desk.py, algo_trade_ui.py) but discarding their monolithic structure. Key principles:

1. **Standalone** — zero dependency on private packages (algo_equity, Webull, OANDA)
2. **Fast first** — mtime caching, SVG charts, no heavy imports on startup
3. **One screen** — five views accessible via pills, no page navigation
4. **Demo-ready** — sample data generator so the UI works out of the box
5. **Production-friendly** — env var overrides for real signal logs

## License

MIT (or your organization's license)

---

Built with ⚡ by the volatility trading team. Questions? See the source or open an issue.
