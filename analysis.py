"""
analysis.py — Cleaning, validation, metrics and interpretation.

Implements the analytical layer Tao integrates into the UI (and which Mert
reviews for correctness):

  * clean_series: drop unusable rows and de-duplicate by year (defensive).
  * annual_series: one value per year, sorted.
  * yoy_changes: year-over-year % change, computed only between *consecutive*
    calendar years. A gap or a zero prior value yields an explicit status
    instead of a misleading number.
  * summary_metrics: totals, average, CAGR, peak/trough.
  * compare_directions: align two directions by year for the comparison chart.
  * interpret: plain-language notes so charts are read correctly.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Cleaning
# ---------------------------------------------------------------------------
def clean_series(records: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[str]]:
    """Return (clean, notes). Drops missing values, de-duplicates by year.

    Never sums duplicates: a duplicated year indicates an upstream problem, so
    we keep the first usable row and surface a note instead of inflating totals.
    """
    notes: List[str] = []
    usable = [r for r in records if r.get("trade_value") is not None]
    dropped = len(records) - len(usable)
    if dropped:
        notes.append(f"{dropped} record(s) without a trade value were excluded (not treated as zero).")

    by_year: Dict[int, Dict[str, Any]] = {}
    dupes = 0
    for r in usable:
        y = int(r["year"])
        if y in by_year:
            dupes += 1
            continue
        by_year[y] = {"year": y, "value": float(r["trade_value"]), "row": r}
    if dupes:
        notes.append(f"{dupes} duplicate year(s) detected; only one value per year was kept (no summing).")

    return [by_year[y] for y in sorted(by_year)], notes


def annual_series(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    series, _ = clean_series(records)
    return series


# ---------------------------------------------------------------------------
# Year-over-year
# ---------------------------------------------------------------------------
def yoy_changes(series: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Compute YOY % change for consecutive calendar years.

    status values:
      ok            -> pct is a valid percentage
      no_prior_year -> previous calendar year has no data (gap)
      prior_zero    -> previous value is 0, growth is undefined
      missing_value -> current year value is missing
    """
    by_year = {int(s["year"]): s.get("value") for s in series}
    out: List[Dict[str, Any]] = []

    for s in series:
        year = int(s["year"])
        value = s.get("value")
        prev_year = year - 1
        prev_value = by_year.get(prev_year)

        item = {
            "year": year,
            "value": value,
            "prev_year": prev_year,
            "prev_value": prev_value,
            "pct": None,
            "status": "ok",
        }

        if value is None:
            item["status"] = "missing_value"
        elif prev_year not in by_year:
            item["status"] = "no_prior_year"
        elif prev_value is None:
            item["status"] = "no_prior_year"
        elif prev_value == 0:
            item["status"] = "prior_zero"
        else:
            item["pct"] = round((value - prev_value) / prev_value * 100.0, 2)

        out.append(item)

    return out


# ---------------------------------------------------------------------------
# Summary metrics
# ---------------------------------------------------------------------------
def summary_metrics(series: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not series:
        return {
            "n_years": 0, "first_year": None, "last_year": None,
            "first_value": None, "latest_value": None,
            "total": 0.0, "average": None, "cagr": None,
            "peak": None, "trough": None,
        }

    values = [s["value"] for s in series if s.get("value") is not None]
    years = [int(s["year"]) for s in series if s.get("value") is not None]
    if not values:
        return {
            "n_years": 0, "first_year": None, "last_year": None,
            "first_value": None, "latest_value": None,
            "total": 0.0, "average": None, "cagr": None,
            "peak": None, "trough": None,
        }

    first_value = values[0]
    latest_value = values[-1]
    n = len(values)

    cagr: Optional[float] = None
    if n > 1 and first_value > 0 and latest_value > 0:
        years_span = years[-1] - years[0]
        if years_span > 0:
            cagr = round(((latest_value / first_value) ** (1.0 / years_span) - 1.0) * 100.0, 2)

    peak_idx = max(range(n), key=lambda i: values[i])
    trough_idx = min(range(n), key=lambda i: values[i])

    return {
        "n_years": n,
        "first_year": years[0],
        "last_year": years[-1],
        "first_value": first_value,
        "latest_value": latest_value,
        "total": float(sum(values)),
        "average": float(sum(values) / n),
        "cagr": cagr,
        "peak": {"year": years[peak_idx], "value": values[peak_idx]},
        "trough": {"year": years[trough_idx], "value": values[trough_idx]},
    }


# ---------------------------------------------------------------------------
# Direction comparison
# ---------------------------------------------------------------------------
def compare_directions(
    series_a: List[Dict[str, Any]],
    series_b: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Align two directions by year. balance = a - b (None if either is missing)."""
    a = {int(s["year"]): s["value"] for s in series_a}
    b = {int(s["year"]): s["value"] for s in series_b}
    years = sorted(set(a) | set(b))
    rows = []
    for y in years:
        va, vb = a.get(y), b.get(y)
        balance = (va - vb) if (va is not None and vb is not None) else None
        rows.append({"year": y, "a": va, "b": vb, "balance": balance})
    return rows


# ---------------------------------------------------------------------------
# Interpretation helpers
# ---------------------------------------------------------------------------
def format_usd(value: Optional[float]) -> str:
    if value is None:
        return "n/a"
    v = float(value)
    for unit, scale in (("T", 1e12), ("B", 1e9), ("M", 1e6), ("K", 1e3)):
        if abs(v) >= scale:
            return f"${v / scale:,.2f}{unit}"
    return f"${v:,.0f}"


def interpret(
    series: List[Dict[str, Any]],
    direction_label: str,
    commodity_label: str,
    valuation: str = "FOB",
) -> List[str]:
    """Plain-language notes so the reader interprets the chart correctly."""
    notes: List[str] = []
    if not series:
        return ["No data to interpret for this selection."]

    metrics = summary_metrics(series)
    yoy = yoy_changes(series)

    notes.append(
        f"Values are annual {valuation} trade values in USD for {commodity_label} "
        f"({direction_label})."
    )

    if metrics["cagr"] is not None:
        trend = "grown" if metrics["cagr"] >= 0 else "declined"
        notes.append(
            f"Between {metrics['first_year']} and {metrics['last_year']}, the value has "
            f"{trend} at roughly {abs(metrics['cagr']):.1f}% per year (CAGR)."
        )

    if metrics["peak"] and metrics["trough"]:
        notes.append(
            f"Peak: {format_usd(metrics['peak']['value'])} in {metrics['peak']['year']}; "
            f"lowest: {format_usd(metrics['trough']['value'])} in {metrics['trough']['year']}."
        )

    # Largest increase / decrease (consecutive years only).
    valid = [y for y in yoy if y["pct"] is not None]
    if valid:
        up = max(valid, key=lambda y: y["pct"])
        down = min(valid, key=lambda y: y["pct"])
        if up["pct"] > 0:
            notes.append(
                f"Largest year-over-year increase: {up['pct']:+.1f}% in {up['year']}."
            )
        if down["pct"] < 0:
            notes.append(
                f"Largest year-over-year decrease: {down['pct']:+.1f}% in {down['year']}."
            )

    gaps = [y["year"] for y in yoy if y["status"] == "no_prior_year"]
    if gaps:
        notes.append(
            "Missing prior-year data prevents a YOY figure for: "
            + ", ".join(str(g) for g in gaps) + " (shown as gaps, never as zero)."
        )

    notes.append(
        "Import and export values can differ between reporting countries because of "
        "CIF/FOB valuation, reporting timing, coverage and classification. Mirror "
        "records are not forced to match."
    )
    return notes
