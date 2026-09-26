"""
Volatility Desk — blazing-fast Streamlit trading performance desk.

Run: streamlit run app.py
"""

from __future__ import annotations

import streamlit as st

from desk.settings_io import get_signal_path, load_settings
from desk.snap import cached_snapshot
from desk.views import render_config, render_cross, render_overall, render_setups, render_tickers

# Page config
st.set_page_config(
    page_title="Volatility Desk",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Dark neon CSS (from neon_desk.py, adapted)
_CSS = """
<style>
/* Base */
.nx { font-family: ui-sans-serif, system-ui, sans-serif; color: #e8fff1; }

/* Hero section */
.nx-hero {
  display: grid;
  grid-template-columns: 120px 1fr auto;
  gap: 0.8rem;
  align-items: end;
  margin: 0 0 0.35rem 0;
}

.nx-live {
  font-size: 1.35rem;
  font-weight: 900;
  letter-spacing: 0.14em;
  padding: 0.35rem 0.5rem;
  border-radius: 8px;
  text-align: center;
}
.nx-live.on {
  color: #39ff14;
  border: 1px solid #39ff14;
  text-shadow: 0 0 14px #39ff14;
  background: #07140a;
}
.nx-live.off {
  color: #ff2d55;
  border: 1px solid #ff2d55;
  text-shadow: 0 0 12px #ff2d55;
  background: #14060a;
}

.nx-pnl {
  font-size: 3.1rem;
  font-weight: 900;
  line-height: 0.9;
  letter-spacing: -0.04em;
}
.nx-pnl.pos { color: #39ff14; text-shadow: 0 0 22px rgba(57,255,20,.55); }
.nx-pnl.neg { color: #ff2d55; text-shadow: 0 0 22px rgba(255,45,85,.5); }
.nx-pnl.flat { color: #00f0ff; text-shadow: 0 0 16px rgba(0,240,255,.4); }

.nx-side {
  text-align: right;
  font-variant-numeric: tabular-nums;
}
.nx-side .k {
  color: #6b7280;
  font-size: 0.68rem;
  letter-spacing: 0.12em;
}
.nx-side .v {
  font-size: 1.15rem;
  font-weight: 800;
}
.nx-side .v.pos { color: #39ff14; }
.nx-side .v.neg { color: #ff2d55; }
.nx-side .v.cyan { color: #00f0ff; }

/* Open position chips */
.nx-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
  min-height: 1.7rem;
  margin: 0.1rem 0 0.6rem 0;
}
.nx-chip {
  border: 1px solid #1c3b28;
  background: #070b09;
  border-radius: 999px;
  padding: 0.12rem 0.55rem;
  font-size: 0.78rem;
  color: #b7ffd0;
}
.nx-chip b { color: #39ff14; }
.nx-chip.short b { color: #ff2bd6; }
.nx-chip.flat {
  color: #5eead4;
  border-color: #134e4a;
}

/* Panel */
.nx-panel {
  background:
    radial-gradient(900px 280px at 12% 0%, rgba(57,255,20,0.10), transparent 55%),
    radial-gradient(700px 240px at 90% 100%, rgba(0,240,255,0.06), transparent 50%),
    #07080d;
  border: 1px solid rgba(57,255,20,0.38);
  border-radius: 18px;
  padding: 14px 16px 6px;
  box-shadow: 0 0 32px rgba(57,255,20,0.07);
}

/* Chart container */
.nx-chart {
  margin-top: 8px;
}
.nx-chart svg {
  display: block;
  width: 100%;
  height: 52vh;
  min-height: 280px;
}

/* Keep sidebar clean */
[data-testid="stSidebar"] [data-testid="stRadio"] label,
[data-testid="stSidebar"] label {
  background: transparent !important;
  border: 0 !important;
  border-radius: 0 !important;
  box-shadow: none !important;
  color: inherit !important;
}
</style>
"""


@st.fragment
def render_desk() -> None:
    """
    Fragment-wrapped desk — navigation clicks stay local, no full rerun.
    """
    st.markdown(_CSS, unsafe_allow_html=True)
    
    # Load snapshot (cached by mtime)
    signal_path = get_signal_path()
    snap = cached_snapshot(signal_path, cache_ttl_sec=2.0)
    
    # Load settings
    settings = load_settings()
    status_live = bool(settings.get("runner_enabled", False))
    
    # Navigation pills
    if "desk_view" not in st.session_state:
        st.session_state["desk_view"] = "Overall"
    
    view_opts = ["Overall", "Setups", "Tickers", "Cross", "Config"]
    
    if hasattr(st, "pills"):
        view = st.pills(
            "View",
            view_opts,
            selection_mode="single",
            key="desk_view",
            label_visibility="collapsed"
        ) or "Overall"
    else:
        view = st.radio(
            "View",
            view_opts,
            horizontal=True,
            key="desk_view",
            label_visibility="collapsed"
        )
    
    # Render selected view
    if view == "Overall":
        render_overall(snap, status_live)
    elif view == "Setups":
        render_setups(snap)
    elif view == "Tickers":
        render_tickers(snap)
    elif view == "Cross":
        render_cross(snap)
    elif view == "Config":
        render_config(snap)


def main() -> None:
    """Main entry point."""
    st.title("⚡ Volatility Desk")
    st.caption("Blazing-fast algo trade performance — one screen, zero lag")
    
    render_desk()
    
    # Footer
    st.markdown("---")
    st.caption(
        "💡 **Tip:** Use env vars `VOLATILITY_DESK_SIGNALS` and `VOLATILITY_DESK_SETTINGS` "
        "to point at real signal logs and config."
    )


if __name__ == "__main__":
    main()
