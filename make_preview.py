"""
make_preview.py — Build a standalone preview.html of the four charts.

Useful for a quick visual check without launching Streamlit. Uses the same
analysis + chart modules as the app, on the bundled sample dataset.

Run:  python make_preview.py
"""

from __future__ import annotations

from pathlib import Path

import analysis
import charts
import comtrade_client
import config

COMMODITY = "9405"
DESC = "Lamps and lighting fittings"
YEARS = list(range(config.DEFAULT_YEAR_MIN, config.DEFAULT_YEAR_MAX + 1))


def series_for(direction_key):
    d = config.direction_meta(direction_key)
    records = []
    for y in YEARS:
        res = comtrade_client.fetch_trade_data(
            reporter=d["reporter_code"], partner=d["partner_code"], year=y,
            flow=d["flow_code"], commodity=COMMODITY, commodity_desc=DESC,
        )
        records.extend([r for r in res.records if int(r.get("is_total", 0)) == 1])
    return analysis.annual_series(records)


def kpi_html(metrics, yoy):
    latest_yoy = next((y for y in reversed(yoy) if y["pct"] is not None), None)
    delta = f"{latest_yoy['pct']:+.1f}% YoY" if latest_yoy else "no prior year"
    cagr = f"{metrics['cagr']:+.1f}%" if metrics["cagr"] is not None else "n/a"
    peak = metrics["peak"]
    cards = [
        (f"Latest value ({metrics['last_year']})", analysis.format_usd(metrics["latest_value"]), delta),
        (f"Total {YEARS[0]}–{YEARS[-1]}", analysis.format_usd(metrics["total"]), ""),
        ("CAGR", cagr, ""),
        ("Peak year", f"{peak['year']}" if peak else "n/a",
         analysis.format_usd(peak["value"]) if peak else ""),
    ]
    out = []
    for label, value, d in cards:
        out.append(
            f'<div class="kpi"><div class="kpi-label">{label}</div>'
            f'<div class="kpi-value">{value}</div>'
            f'<div class="kpi-delta">{d}</div></div>'
        )
    return "".join(out)


def main() -> None:
    tr = series_for("TR_TO_CN")
    cn = series_for("CN_TO_TR")
    metrics = analysis.summary_metrics(tr)
    yoy = analysis.yoy_changes(tr)
    rows = analysis.compare_directions(tr, cn)

    f1 = charts.annual_value_line(tr, f"Annual trade value — {COMMODITY} {DESC}",
                                  "Türkiye → China", "FOB")
    f2 = charts.yoy_bar(yoy, f"Year-over-year change — {COMMODITY}")
    f3 = charts.direction_comparison(rows, "Türkiye → China", "China → Türkiye")
    f4 = charts.balance_chart(rows, "Türkiye → China", "China → Türkiye")

    parts = []
    for i, fig in enumerate([f1, f2, f3, f4]):
        parts.append(fig.to_html(full_html=False, include_plotlyjs=("cdn" if i == 0 else False),
                                 config={"displayModeBar": False}))

    html = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<title>Türkiye–China Trade Explorer — Preview</title>
<style>
  body {{ background:#0e1117; color:#e6e6e6; font-family:-apple-system,Segoe UI,Roboto,sans-serif;
         margin:0; padding:32px; }}
  h1 {{ font-size:1.9rem; margin:0 0 4px; }}
  .sub {{ color:#9aa4b2; margin:0 0 24px; }}
  .kpis {{ display:flex; gap:16px; flex-wrap:wrap; margin-bottom:24px; }}
  .kpi {{ background:#161b22; border:1px solid #2a2f3a; border-radius:12px;
          padding:16px 20px; min-width:180px; }}
  .kpi-label {{ color:#9aa4b2; font-size:0.8rem; }}
  .kpi-value {{ font-size:1.6rem; font-weight:700; margin-top:6px; }}
  .kpi-delta {{ color:#5ee08a; font-size:0.85rem; margin-top:4px; min-height:1em; }}
  .card {{ background:#161b22; border:1px solid #2a2f3a; border-radius:12px;
           padding:8px; margin-bottom:20px; }}
  .foot {{ color:#6b7480; font-size:0.78rem; margin-top:20px; }}
</style></head>
<body>
  <h1>🌐 Türkiye–China Trade Explorer</h1>
  <p class="sub">Preview · HS {COMMODITY} — {DESC} · {config.DEFAULT_YEAR_MIN}–{config.DEFAULT_YEAR_MAX} · sample dataset</p>
  <div class="kpis">{kpi_html(metrics, yoy)}</div>
  {''.join(f'<div class="card">{p}</div>' for p in parts)}
  <p class="foot">Source: UN Comtrade. Availability and values depend on reporting-country
  submissions and may be revised. Import/export records may differ due to valuation and
  reporting practices. Missing years are shown as gaps, never as zero.</p>
</body></html>"""

    out = Path(__file__).resolve().parent / "preview.html"
    out.write_text(html, encoding="utf-8")
    print("wrote", out)


if __name__ == "__main__":
    main()
