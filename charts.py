"""
charts.py — Reusable Plotly figures.

Three charts the MVP needs:
  * annual_value_line   — annual trade value (line, gaps for missing years)
  * yoy_bar             — year-over-year % change (signed bars)
  * direction_comparison— both directions side by side (country comparison)

All figures carry a source annotation and explicit USD units, and missing
years are drawn as gaps (connectgaps=False) so they are never mistaken for zero.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import plotly.graph_objects as go

# Dark palette (matches the app's dark theme).
BG = "#0e1117"
PANEL = "#161b22"
GRID = "#2a2f3a"
TEXT = "#e6e6e6"
MUTED = "#9aa4b2"
ACCENT = "#4da3ff"
UP = "#ff5c5c"    # increase — red (Chinese market convention)
DOWN = "#2ecc71"  # decrease — green

SOURCE_NOTE = (
    "Source: UN Comtrade. Availability and values depend on reporting-country "
    "submissions and may be revised. Import/export records may differ due to "
    "valuation and reporting practices."
)


def _fmt_usd(value: Optional[float]) -> str:
    if value is None:
        return "n/a"
    v = float(value)
    for unit, scale in (("T", 1e12), ("B", 1e9), ("M", 1e6), ("K", 1e3)):
        if abs(v) >= scale:
            return f"${v / scale:,.2f}{unit}"
    return f"${v:,.0f}"


def _apply_theme(fig: go.Figure, height: int = 420) -> go.Figure:
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor=BG,
        plot_bgcolor=PANEL,
        font=dict(color=TEXT, size=13),
        margin=dict(l=10, r=10, t=50, b=70),
        height=height,
        hoverlabel=dict(bgcolor=PANEL, font_color=TEXT, bordercolor=GRID),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    )
    fig.update_xaxes(gridcolor=GRID, zerolinecolor=GRID, linecolor=GRID)
    fig.update_yaxes(gridcolor=GRID, zerolinecolor=GRID, linecolor=GRID)
    fig.add_annotation(
        text=SOURCE_NOTE,
        xref="paper", yref="paper", x=0, y=-0.28,
        showarrow=False, font=dict(size=10, color=MUTED), align="left",
    )
    return fig


def annual_value_line(
    series: List[Dict[str, Any]],
    title: str,
    direction_label: str,
    valuation: str = "FOB",
) -> go.Figure:
    """Annual trade value with a continuous year axis (missing years = gaps)."""
    if not series:
        fig = go.Figure()
        fig.add_annotation(text="No data available for this selection",
                           x=0.5, y=0.5, xref="paper", yref="paper",
                           showarrow=False, font=dict(size=16, color=MUTED))
        return _apply_theme(fig)

    years_all = [s["year"] for s in series]
    y_min, y_max = min(years_all), max(years_all)
    value_map = {int(s["year"]): s["value"] for s in series}
    years = list(range(y_min, y_max + 1))
    values = [value_map.get(y) for y in years]

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=years,
            y=values,
            mode="lines+markers",
            name=direction_label,
            line=dict(color=ACCENT, width=3),
            marker=dict(size=7, color=ACCENT),
            connectgaps=False,
            customdata=[[_fmt_usd(v)] for v in values],
            hovertemplate="Year %{x}<br>Value %{customdata[0]}<extra></extra>",
        )
    )
    fig.update_layout(title=dict(text=title, font=dict(size=16)))
    fig.update_xaxes(title_text="Year", dtick=1, tickangle=-45)
    fig.update_yaxes(title_text=f"Trade value (USD, {valuation})",
                     tickprefix="$", tickformat=",.2s")
    return _apply_theme(fig)


def yoy_bar(yoy: List[Dict[str, Any]], title: str = "Year-over-year change") -> go.Figure:
    """Signed bar chart of YOY % change. Red = increase, green = decrease."""
    valid = [y for y in yoy if y.get("pct") is not None]
    if not valid:
        fig = go.Figure()
        fig.add_annotation(
            text="No valid year-over-year change (missing or zero prior values)",
            x=0.5, y=0.5, xref="paper", yref="paper",
            showarrow=False, font=dict(size=14, color=MUTED),
        )
        return _apply_theme(fig)

    years = [y["year"] for y in valid]
    pcts = [y["pct"] for y in valid]
    colors = [UP if p >= 0 else DOWN for p in pcts]

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=years,
            y=pcts,
            marker_color=colors,
            text=[f"{p:+.1f}%" for p in pcts],
            textposition="outside",
            cliponaxis=False,
            customdata=[[_fmt_usd(y.get("prev_value")), _fmt_usd(y.get("value"))] for y in valid],
            hovertemplate=(
                "Year %{x}<br>Change %{y:+.2f}%<br>"
                "Previous %{customdata[0]}<br>Current %{customdata[1]}<extra></extra>"
            ),
        )
    )
    fig.update_layout(title=dict(text=title, font=dict(size=16)), showlegend=False)
    fig.update_xaxes(title_text="Year", dtick=1, tickangle=-45)
    fig.update_yaxes(title_text="Change (%)", ticksuffix="%", zeroline=True,
                     zerolinecolor=TEXT, zerolinewidth=1)
    return _apply_theme(fig)


def direction_comparison(
    rows: List[Dict[str, Any]],
    label_a: str,
    label_b: str,
    log_scale: bool = False,
) -> go.Figure:
    """Grouped bars comparing both trade directions by year."""
    if not rows:
        fig = go.Figure()
        fig.add_annotation(text="No comparison data available",
                           x=0.5, y=0.5, xref="paper", yref="paper",
                           showarrow=False, font=dict(size=16, color=MUTED))
        return _apply_theme(fig)

    years = [r["year"] for r in rows]
    a_vals = [r["a"] for r in rows]
    b_vals = [r["b"] for r in rows]

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=years, y=a_vals, name=label_a, marker_color=ACCENT,
            customdata=[[_fmt_usd(v)] for v in a_vals],
            hovertemplate="Year %{x}<br>" + label_a + ": %{customdata[0]}<extra></extra>",
        )
    )
    fig.add_trace(
        go.Bar(
            x=years, y=b_vals, name=label_b, marker_color=UP,
            customdata=[[_fmt_usd(v)] for v in b_vals],
            hovertemplate="Year %{x}<br>" + label_b + ": %{customdata[0]}<extra></extra>",
        )
    )
    fig.update_layout(
        title=dict(text="Trade direction comparison", font=dict(size=16)),
        barmode="group",
    )
    fig.update_xaxes(title_text="Year", dtick=1, tickangle=-45)
    fig.update_yaxes(
        title_text="Trade value (USD)", tickprefix="$", tickformat=",.2s",
        type="log" if log_scale else "linear",
    )
    return _apply_theme(fig)


def balance_chart(rows: List[Dict[str, Any]], label_a: str, label_b: str) -> go.Figure:
    """Trade balance (a - b) per year as a signed line/bar."""
    valid = [r for r in rows if r.get("balance") is not None]
    if not valid:
        fig = go.Figure()
        fig.add_annotation(text="No balance data available",
                           x=0.5, y=0.5, xref="paper", yref="paper",
                           showarrow=False, font=dict(size=16, color=MUTED))
        return _apply_theme(fig)

    years = [r["year"] for r in valid]
    balances = [r["balance"] for r in valid]
    colors = [UP if b >= 0 else DOWN for b in balances]

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=years, y=balances, marker_color=colors,
            customdata=[[_fmt_usd(b)] for b in balances],
            hovertemplate="Year %{x}<br>Balance " + label_a + " − " + label_b +
                          ": %{customdata[0]}<extra></extra>",
        )
    )
    fig.update_layout(
        title=dict(text=f"Trade balance ({label_a} minus {label_b})", font=dict(size=16)),
        showlegend=False,
    )
    fig.update_xaxes(title_text="Year", dtick=1, tickangle=-45)
    fig.update_yaxes(title_text="Balance (USD)", tickprefix="$", tickformat=",.2s",
                     zeroline=True, zerolinecolor=TEXT)
    return _apply_theme(fig)
