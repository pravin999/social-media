"""SVG chart generation - blazing fast, no Plotly/matplotlib on hot path."""

from __future__ import annotations

from typing import Dict, List, Tuple


def svg_frame(inner: str, *, w: int = 1000, h: int = 420) -> str:
    """Wrap SVG content in viewBox frame."""
    return (
        f'<svg viewBox="0 0 {w} {h}" width="100%" role="img" preserveAspectRatio="xMidYMid meet">'
        f'<rect x="0" y="0" width="{w}" height="{h}" rx="12" fill="#05060a"/>'
        f"{inner}</svg>"
    )


def svg_equity_curve(vals: List[float]) -> str:
    """
    Generate SVG line + area chart for equity curve.
    Fast rendering: no external libs, pure SVG markup.
    """
    w, h = 1000, 420
    
    if len(vals) < 2:
        return svg_frame(
            '<text x="40" y="220" fill="#00f0ff" font-size="28" '
            'font-family="ui-sans-serif,sans-serif">FLAT</text>'
        )
    
    lo, hi = min(vals), max(vals)
    pad = max((hi - lo) * 0.12, 0.5)
    lo, hi = lo - pad, hi + pad
    span = (hi - lo) or 1.0
    left, right, top, bot = 56, 16, 16, 28
    
    def xy(i: int, v: float) -> Tuple[float, float]:
        x = left + (w - left - right) * (i / (len(vals) - 1))
        y = top + (h - top - bot) * (1 - (v - lo) / span)
        return x, y
    
    pts = [xy(i, v) for i, v in enumerate(vals)]
    
    # Polyline path
    d = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    
    # Area fill path
    x0, _y0 = pts[0]
    xn, yn = pts[-1]
    area = (
        f"M {pts[0][0]:.1f},{pts[0][1]:.1f} "
        + " ".join(f"L {x:.1f},{y:.1f}" for x, y in pts[1:])
        + f" L {xn:.1f},{h - bot:.1f} L {x0:.1f},{h - bot:.1f} Z"
    )
    
    last = vals[-1]
    stroke = "#39ff14" if last >= 0 else "#ff2d55"
    fill = "rgba(57,255,20,0.18)" if last >= 0 else "rgba(255,45,85,0.16)"
    
    # Grid lines
    grid = []
    for g in range(4):
        gy = top + (h - top - bot) * g / 3
        val = hi - (hi - lo) * g / 3
        grid.append(
            f'<line x1="{left}" y1="{gy:.1f}" x2="{w - right}" y2="{gy:.1f}" stroke="#142018"/>'
            f'<text x="6" y="{gy + 4:.1f}" fill="#4b5563" font-size="12" '
            f'font-family="ui-sans-serif,sans-serif">{val:+.0f}</text>'
        )
    
    # Zero line
    zero = ""
    if lo < 0 < hi:
        zy = top + (h - top - bot) * (1 - (0 - lo) / span)
        zero = (
            f'<line x1="{left}" y1="{zy:.1f}" x2="{w - right}" y2="{zy:.1f}" '
            f'stroke="#1f2937" stroke-dasharray="5 6"/>'
        )
    
    return svg_frame(
        f'''
        {''.join(grid)}{zero}
        <path d="{area}" fill="{fill}"/>
        <polyline fill="none" stroke="{stroke}" stroke-width="3" points="{d}"/>
        <circle cx="{xn:.1f}" cy="{yn:.1f}" r="5" fill="{stroke}"/>
        <text x="{max(left, xn - 78):.1f}" y="{max(28, yn - 12):.1f}" fill="{stroke}" 
              font-size="16" font-weight="700" font-family="ui-sans-serif,sans-serif">${last:+.2f}</text>
        '''
    )


def svg_bars(pairs: List[Tuple[str, float]]) -> str:
    """
    Generate SVG bar chart for labeled values (setup/ticker PnL).
    Fast rendering: no external libs.
    """
    w, h = 1000, 420
    
    if not pairs:
        return svg_frame(
            '<text x="40" y="220" fill="#00f0ff" font-size="28" '
            'font-family="ui-sans-serif,sans-serif">—</text>'
        )
    
    peak = max(abs(v) for _, v in pairs) or 1.0
    n = len(pairs)
    left, gap, bot = 16, 14, 36
    bw = max(22, (w - left * 2 - gap * max(n - 1, 0)) / max(n, 1))
    mid = (h - bot) / 2 + 8
    
    parts = [
        f'<line x1="12" y1="{mid:.1f}" x2="{w - 12}" y2="{mid:.1f}" stroke="#1f2937"/>'
    ]
    
    for i, (lab, v) in enumerate(pairs):
        x = left + i * (bw + gap)
        bh = (abs(v) / peak) * (mid - 36)
        y = mid - bh if v >= 0 else mid
        color = "#39ff14" if v >= 0 else "#ff2d55"
        ty = y - 8 if v >= 0 else y + bh + 16
        
        parts.append(
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{bw:.1f}" height="{max(bh, 2):.1f}" '
            f'rx="6" fill="{color}"/>'
            f'<text x="{x + bw / 2:.1f}" y="{ty:.1f}" text-anchor="middle" fill="{color}" '
            f'font-size="13" font-family="ui-sans-serif,sans-serif">{v:+.0f}</text>'
            f'<text x="{x + bw / 2:.1f}" y="{h - 12}" text-anchor="middle" fill="#9ca3af" '
            f'font-size="13" font-family="ui-sans-serif,sans-serif">{lab}</text>'
        )
    
    return svg_frame("".join(parts))


def svg_heatmap(
    data: Dict[str, Dict[str, float]],
    *,
    max_rows: int = 10,
    max_cols: int = 15
) -> str:
    """
    Generate SVG heatmap for setup × ticker cross-tab.
    Rows = setups, Cols = tickers, cells colored by PnL.
    """
    w, h = 1000, 420
    
    if not data:
        return svg_frame(
            '<text x="40" y="220" fill="#00f0ff" font-size="28" '
            'font-family="ui-sans-serif,sans-serif">—</text>'
        )
    
    # Flatten and sort
    setups = sorted(data.keys())[:max_rows]
    all_tickers = set()
    for setup in setups:
        all_tickers.update(data[setup].keys())
    tickers = sorted(all_tickers, key=lambda t: sum(data.get(s, {}).get(t, 0) for s in setups), reverse=True)[:max_cols]
    
    if not setups or not tickers:
        return svg_frame(
            '<text x="40" y="220" fill="#00f0ff" font-size="24" '
            'font-family="ui-sans-serif,sans-serif">No data</text>'
        )
    
    # Layout
    left_margin = 80
    top_margin = 40
    cell_w = min(60, (w - left_margin - 20) / len(tickers))
    cell_h = min(50, (h - top_margin - 20) / len(setups))
    
    # Find color scale
    all_vals = [v for s in setups for v in data[s].values()]
    vmax = max(abs(v) for v in all_vals) if all_vals else 1.0
    
    def color_for_pnl(pnl: float) -> str:
        """Green for positive, red for negative, intensity by magnitude."""
        if abs(pnl) < 0.01:
            return "#1a1a1a"
        ratio = min(abs(pnl) / vmax, 1.0)
        if pnl > 0:
            # Green scale
            g = int(100 + 155 * ratio)
            return f"rgb(0,{g},0)"
        else:
            # Red scale
            r = int(100 + 155 * ratio)
            return f"rgb({r},0,0)"
    
    parts = []
    
    # Row labels (setups)
    for i, setup in enumerate(setups):
        y = top_margin + i * cell_h + cell_h / 2 + 4
        parts.append(
            f'<text x="{left_margin - 8}" y="{y:.1f}" text-anchor="end" fill="#9ca3af" '
            f'font-size="12" font-family="ui-sans-serif,sans-serif">{setup}</text>'
        )
    
    # Column labels (tickers)
    for j, ticker in enumerate(tickers):
        x = left_margin + j * cell_w + cell_w / 2
        parts.append(
            f'<text x="{x:.1f}" y="{top_margin - 8}" text-anchor="middle" fill="#9ca3af" '
            f'font-size="11" font-family="ui-sans-serif,sans-serif">{ticker}</text>'
        )
    
    # Cells
    for i, setup in enumerate(setups):
        for j, ticker in enumerate(tickers):
            pnl = data[setup].get(ticker, 0.0)
            x = left_margin + j * cell_w
            y = top_margin + i * cell_h
            
            fill = color_for_pnl(pnl)
            parts.append(
                f'<rect x="{x:.1f}" y="{y:.1f}" width="{cell_w:.1f}" height="{cell_h:.1f}" '
                f'fill="{fill}" stroke="#0a0a0a" stroke-width="1"/>'
            )
            
            # Show value if non-zero
            if abs(pnl) >= 0.01:
                tx = x + cell_w / 2
                ty = y + cell_h / 2 + 4
                text_color = "#ffffff" if abs(pnl) > vmax * 0.3 else "#cccccc"
                parts.append(
                    f'<text x="{tx:.1f}" y="{ty:.1f}" text-anchor="middle" fill="{text_color}" '
                    f'font-size="10" font-family="ui-monospace,monospace">{pnl:+.0f}</text>'
                )
    
    return svg_frame("".join(parts), w=w, h=h)
