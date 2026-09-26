"""UI views: Overall, Setups, Tickers, Cross, Config."""

from __future__ import annotations

from typing import Any, Dict, List

import streamlit as st

from .charts_svg import svg_bars, svg_equity_curve, svg_heatmap
from .settings_io import load_settings, save_settings


def render_overall(snap: Dict[str, Any], status_live: bool) -> None:
    """
    Overall view: hero PnL, KPIs, open positions, equity curve.
    """
    total = float(snap["total_pnl"])
    today = float(snap["today_pnl"])
    wr = snap["win_rate"]
    n = snap["n"]
    
    # Status badge
    live_cls = "on" if status_live else "off"
    live_text = "LIVE" if status_live else "DEMO"
    
    # Hero section
    pnl_cls = "pos" if total > 0 else ("neg" if total < 0 else "flat")
    today_cls = "pos" if today > 0 else ("neg" if today < 0 else "cyan")
    wr_s = f"{wr:.0f}%" if wr is not None else "—"
    
    st.markdown(
        f'''
        <div class="nx">
          <div class="nx-panel">
            <div class="nx-hero">
              <div class="nx-live {live_cls}">{live_text}</div>
              <div class="nx-pnl {pnl_cls}">${total:+,.2f}</div>
              <div class="nx-side">
                <div class="k">TODAY</div><div class="v {today_cls}">${today:+,.2f}</div>
                <div class="k">WIN</div><div class="v cyan">{wr_s}</div>
                <div class="k">N</div><div class="v cyan">{n}</div>
              </div>
            </div>
          </div>
        </div>
        ''',
        unsafe_allow_html=True
    )
    
    # Open positions
    opens = snap.get("open_positions") or []
    if opens:
        st.markdown("**Open positions**")
        chips = []
        for op in opens[:12]:
            side_cls = "short" if op["side"] == "sell" else ""
            chips.append(
                f'<span class="nx-chip {side_cls}">{op["setup"]} '
                f'<b>{op["symbol"]}</b> {op["side"]}</span>'
            )
        st.markdown(f'<div class="nx-chips">{"".join(chips)}</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="nx-chips"><span class="nx-chip flat">FLAT</span></div>', unsafe_allow_html=True)
    
    # Chart pills (fragment-local state)
    if "overall_chart" not in st.session_state:
        st.session_state["overall_chart"] = "Curve"
    
    chart_opts = ["Curve", "By setup", "By ticker", "By day"]
    
    if hasattr(st, "pills"):
        chart = st.pills(
            "Chart",
            chart_opts,
            selection_mode="single",
            key="overall_chart",
            label_visibility="collapsed"
        ) or "Curve"
    else:
        chart = st.radio(
            "Chart",
            chart_opts,
            horizontal=True,
            key="overall_chart",
            label_visibility="collapsed"
        )
    
    # Render selected chart
    if chart == "By setup":
        pairs = sorted(
            [(k, v["pnl"]) for k, v in (snap.get("by_setup") or {}).items()],
            key=lambda x: abs(x[1]),
            reverse=True
        )[:10]
        svg = svg_bars(pairs)
    elif chart == "By ticker":
        pairs = sorted(
            [(k, v["pnl"]) for k, v in (snap.get("by_ticker") or {}).items()],
            key=lambda x: abs(x[1]),
            reverse=True
        )[:10]
        svg = svg_bars(pairs)
    elif chart == "By day":
        by_day = snap.get("by_day") or {}
        days = sorted(by_day.items())[-12:]
        pairs = [(d[5:], v) for d, v in days]
        svg = svg_bars(pairs)
    else:  # Curve
        svg = svg_equity_curve(snap.get("equity") or [])
    
    st.markdown(f'<div class="nx-chart">{svg}</div>', unsafe_allow_html=True)


def render_setups(snap: Dict[str, Any]) -> None:
    """
    Setups view: ranked table + chart, drill-down to ticker breakdown.
    """
    by_setup = snap.get("by_setup") or {}
    
    if not by_setup:
        st.info("No setup data yet.")
        return
    
    # Build ranked table
    rows = []
    for setup, stats in by_setup.items():
        pnl = stats["pnl"]
        n = stats["n"]
        wins = stats["wins"]
        wr = (100.0 * wins / n) if n else 0.0
        avg_hold_sec = stats["hold_sec"] / n if n else 0.0
        avg_hold_min = avg_hold_sec / 60.0
        
        rows.append({
            "Setup": setup,
            "PnL": f"${pnl:+.2f}",
            "Trades": n,
            "Win%": f"{wr:.0f}%",
            "Avg hold": f"{avg_hold_min:.0f}m"
        })
    
    # Sort by |PnL|
    rows.sort(key=lambda r: abs(float(r["PnL"].replace("$", "").replace("+", ""))), reverse=True)
    
    st.markdown("**Setup rankings**")
    st.dataframe(rows, use_container_width=True, hide_index=True)
    
    # Bar chart
    pairs = [(r["Setup"], float(r["PnL"].replace("$", "").replace("+", ""))) for r in rows[:8]]
    svg = svg_bars(pairs)
    st.markdown(f'<div class="nx-chart">{svg}</div>', unsafe_allow_html=True)
    
    # Drill-down: select setup to see ticker breakdown
    st.markdown("---")
    st.markdown("**Drill-down: setup → tickers**")
    setup_names = [r["Setup"] for r in rows]
    
    selected_setup = st.selectbox("Select setup", setup_names, key="setup_drill")
    
    if selected_setup:
        by_setup_ticker = snap.get("by_setup_ticker") or {}
        ticker_pnls = by_setup_ticker.get(selected_setup) or {}
        
        if ticker_pnls:
            ticker_rows = [
                {"Ticker": t, "PnL": f"${p:+.2f}"}
                for t, p in sorted(ticker_pnls.items(), key=lambda x: abs(x[1]), reverse=True)
            ]
            st.dataframe(ticker_rows, use_container_width=True, hide_index=True)
        else:
            st.caption(f"No ticker breakdown for {selected_setup}")


def render_tickers(snap: Dict[str, Any]) -> None:
    """
    Tickers view: ranked table + chart, drill-down to setup breakdown.
    """
    by_ticker = snap.get("by_ticker") or {}
    
    if not by_ticker:
        st.info("No ticker data yet.")
        return
    
    # Build ranked table
    rows = []
    for ticker, stats in by_ticker.items():
        pnl = stats["pnl"]
        n = stats["n"]
        wins = stats["wins"]
        wr = (100.0 * wins / n) if n else 0.0
        avg_hold_sec = stats["hold_sec"] / n if n else 0.0
        avg_hold_min = avg_hold_sec / 60.0
        
        rows.append({
            "Ticker": ticker,
            "PnL": f"${pnl:+.2f}",
            "Trades": n,
            "Win%": f"{wr:.0f}%",
            "Avg hold": f"{avg_hold_min:.0f}m"
        })
    
    # Sort by |PnL|
    rows.sort(key=lambda r: abs(float(r["PnL"].replace("$", "").replace("+", ""))), reverse=True)
    
    st.markdown("**Ticker rankings**")
    st.dataframe(rows, use_container_width=True, hide_index=True)
    
    # Bar chart
    pairs = [(r["Ticker"], float(r["PnL"].replace("$", "").replace("+", ""))) for r in rows[:10]]
    svg = svg_bars(pairs)
    st.markdown(f'<div class="nx-chart">{svg}</div>', unsafe_allow_html=True)
    
    # Drill-down: select ticker to see setup breakdown
    st.markdown("---")
    st.markdown("**Drill-down: ticker → setups**")
    ticker_names = [r["Ticker"] for r in rows]
    
    selected_ticker = st.selectbox("Select ticker", ticker_names, key="ticker_drill")
    
    if selected_ticker:
        by_setup_ticker = snap.get("by_setup_ticker") or {}
        setup_pnls: Dict[str, float] = {}
        for setup, tickers in by_setup_ticker.items():
            if selected_ticker in tickers:
                setup_pnls[setup] = tickers[selected_ticker]
        
        if setup_pnls:
            setup_rows = [
                {"Setup": s, "PnL": f"${p:+.2f}"}
                for s, p in sorted(setup_pnls.items(), key=lambda x: abs(x[1]), reverse=True)
            ]
            st.dataframe(setup_rows, use_container_width=True, hide_index=True)
        else:
            st.caption(f"No setup breakdown for {selected_ticker}")


def render_cross(snap: Dict[str, Any]) -> None:
    """
    Cross-tab view: setup × ticker matrix heatmap + detail panel.
    """
    by_setup_ticker = snap.get("by_setup_ticker") or {}
    
    if not by_setup_ticker:
        st.info("No cross-tab data yet.")
        return
    
    st.markdown("**Setup × Ticker matrix**")
    st.caption("Rows = setups, Cols = tickers, Color intensity = |PnL|")
    
    svg = svg_heatmap(by_setup_ticker, max_rows=10, max_cols=15)
    st.markdown(f'<div class="nx-chart">{svg}</div>', unsafe_allow_html=True)
    
    # Detail panel: select setup + ticker
    st.markdown("---")
    st.markdown("**Detail panel**")
    
    setup_names = sorted(by_setup_ticker.keys())
    
    if not setup_names:
        st.caption("No data")
        return
    
    c1, c2 = st.columns(2)
    with c1:
        sel_setup = st.selectbox("Setup", setup_names, key="cross_setup")
    
    if sel_setup:
        ticker_names = sorted(by_setup_ticker[sel_setup].keys())
        with c2:
            sel_ticker = st.selectbox("Ticker", ticker_names, key="cross_ticker") if ticker_names else None
        
        if sel_ticker:
            pnl = by_setup_ticker[sel_setup][sel_ticker]
            st.metric(f"{sel_setup} × {sel_ticker}", f"${pnl:+.2f}")


def render_config(snap: Dict[str, Any]) -> None:
    """
    Config view: strategy toggles, ticker lists, sizing, save/stub status.
    """
    settings = load_settings()
    algos = settings.get("algos") or {}
    
    st.markdown("**Strategy configuration**")
    st.caption("Toggle strategies, set tickers, and adjust sizing. Changes save to settings.json.")
    
    with st.form("config_form", clear_on_submit=False):
        # Global toggles
        st.markdown("**Global**")
        c1, c2, c3 = st.columns(3)
        with c1:
            runner_enabled = st.toggle("Accept entries", value=bool(settings.get("runner_enabled", False)))
        with c2:
            allow_long = st.checkbox("Allow long", value=bool(settings.get("allow_long", True)))
        with c3:
            allow_short = st.checkbox("Allow short", value=bool(settings.get("allow_short", True)))
        
        st.markdown("---")
        
        # Per-strategy config
        updated_algos: Dict[str, Any] = {}
        
        for algo_id, algo_meta in algos.items():
            label = algo_meta.get("label", algo_id)
            enabled = algo_meta.get("enabled", False)
            tickers = algo_meta.get("tickers") or []
            
            st.markdown(f"**{label}** (`{algo_id}`)")
            
            col_a, col_b = st.columns([1, 3])
            with col_a:
                new_enabled = st.toggle(f"Enable {label}", value=enabled, key=f"cfg_{algo_id}_on")
            with col_b:
                new_tickers_csv = st.text_input(
                    f"Tickers for {label}",
                    value=", ".join(tickers),
                    key=f"cfg_{algo_id}_tickers",
                    placeholder="SMCI, SOFI, RDW"
                )
            
            # Parse tickers
            new_tickers = [
                t.strip().upper().lstrip("$")
                for t in new_tickers_csv.split(",")
                if t.strip()
            ]
            
            # Per-strategy params (example: fund_pct for GEX, max_notional for VWAP)
            extra_cols = st.columns(3)
            extra_params: Dict[str, Any] = {}
            
            if "GEX" in algo_id.upper():
                with extra_cols[0]:
                    fund_pct = st.number_input(
                        "Fund %",
                        min_value=5.0,
                        max_value=100.0,
                        value=float(algo_meta.get("fund_pct", 50.0)),
                        step=5.0,
                        key=f"cfg_{algo_id}_fund"
                    )
                    extra_params["fund_pct"] = fund_pct
                with extra_cols[1]:
                    min_conf = st.number_input(
                        "Min conf %",
                        min_value=0.0,
                        max_value=100.0,
                        value=float(algo_meta.get("min_conf", 10.0)),
                        step=1.0,
                        key=f"cfg_{algo_id}_conf"
                    )
                    extra_params["min_conf"] = min_conf
                with extra_cols[2]:
                    hold_days = st.number_input(
                        "Max hold days",
                        min_value=1,
                        max_value=20,
                        value=int(algo_meta.get("max_hold_days", 5)),
                        key=f"cfg_{algo_id}_hold"
                    )
                    extra_params["max_hold_days"] = hold_days
            
            elif "VWAP" in algo_id.upper():
                with extra_cols[0]:
                    max_notional = st.number_input(
                        "Max $",
                        min_value=10.0,
                        max_value=10000.0,
                        value=float(algo_meta.get("max_notional", 100.0)),
                        step=10.0,
                        key=f"cfg_{algo_id}_notional"
                    )
                    extra_params["max_notional"] = max_notional
            
            elif "IWM" in algo_id.upper() or "WISH" in algo_id.upper():
                with extra_cols[0]:
                    contracts = st.number_input(
                        "Contracts",
                        min_value=1,
                        max_value=20,
                        value=int(algo_meta.get("contracts", 1)),
                        key=f"cfg_{algo_id}_contracts"
                    )
                    extra_params["contracts"] = contracts
            
            elif "RSI" in algo_id.upper():
                with extra_cols[0]:
                    shares = st.number_input(
                        "Shares",
                        min_value=1,
                        max_value=20,
                        value=int(algo_meta.get("shares", 2)),
                        key=f"cfg_{algo_id}_shares"
                    )
                    extra_params["shares"] = shares
            
            updated_algos[algo_id] = {
                **algo_meta,
                "enabled": new_enabled,
                "tickers": new_tickers,
                **extra_params
            }
            
            st.markdown("---")
        
        # Save button
        submitted = st.form_submit_button("Save configuration", type="primary")
    
    if submitted:
        # Validate
        if not allow_long and not allow_short:
            st.error("At least one of Allow long / Allow short must be checked.")
        else:
            # Save
            save_settings({
                "runner_enabled": runner_enabled,
                "allow_long": allow_long,
                "allow_short": allow_short,
                "algos": updated_algos
            })
            st.success("Configuration saved!")
            st.rerun()
    
    # Status display
    st.markdown("---")
    st.markdown("**Status**")
    
    # Stub: show DEMO or LIVE based on runner_enabled
    status = "LIVE" if settings.get("runner_enabled") else "DEMO"
    status_color = "green" if settings.get("runner_enabled") else "orange"
    
    st.markdown(
        f'<div style="padding: 0.5rem 1rem; background: rgba(0,0,0,0.3); '
        f'border-left: 4px solid {status_color}; border-radius: 4px;">'
        f'<strong>Mode:</strong> {status}<br/>'
        f'<small>This is a demo desk. Real broker integration not included in v1.</small>'
        f'</div>',
        unsafe_allow_html=True
    )
    
    # Show current KPIs
    st.markdown("**Current snapshot KPIs**")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total PnL", f"${snap['total_pnl']:+.2f}")
    col2.metric("Today PnL", f"${snap['today_pnl']:+.2f}")
    col3.metric("Win rate", f"{snap['win_rate']:.0f}%" if snap['win_rate'] else "—")
    col4.metric("Trades", snap['n'])
