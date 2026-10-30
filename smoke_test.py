"""
smoke_test.py — End-to-end check of the data pipeline (no UI).

Exercises: fetch -> ingest -> idempotent re-ingest -> query -> analysis ->
charts -> validation, for both directions and several products.

Run:  python smoke_test.py
"""

from __future__ import annotations

import os
from pathlib import Path
from types import SimpleNamespace

# Tests use the deterministic sample dataset (fast, offline, no rate limits).
os.environ.setdefault("USE_SAMPLE_DATA", "1")

import analysis
import charts
import comtrade_client
import config
import database

TEST_DB = config.DATA_DIR / "test_trade.db"


def ingest_direction(conn, direction_key, commodity, years, desc):
    d = config.direction_meta(direction_key)
    payloads = []
    for y in years:
        res = comtrade_client.fetch_trade_data(
            reporter=d["reporter_code"], partner=d["partner_code"], year=y,
            flow=d["flow_code"], commodity=commodity, commodity_desc=desc,
        )
        database.upsert_records(conn, res)
        payloads.append(res)
    return payloads


def main() -> None:
    if TEST_DB.exists():
        TEST_DB.unlink()
    conn = database.get_connection(TEST_DB)
    database.init_db(conn)

    commodity = "9405"
    desc = "Lamps and lighting fittings"
    years = list(range(config.DEFAULT_YEAR_MIN, config.DEFAULT_YEAR_MAX + 1))
    n_years = len(years)

    print("== Ingesting TR->CN and CN->TR for", commodity, "==")
    ingest_direction(conn, "TR_TO_CN", commodity, years, desc)
    ingest_direction(conn, "CN_TO_TR", commodity, years, desc)

    cts = database.counts(conn)
    print("counts after first ingest:", cts)
    assert cts["total_rows"] == n_years * 2, (
        f"expected {n_years * 2} total rows, got {cts['total_rows']}")
    # one total per year per direction; breakdown rows archived in raw_records only
    assert cts["raw_rows"] == n_years * 2 * 4, (
        f"expected {n_years * 8} raw rows, got {cts['raw_rows']}")

    print("\n== Re-ingesting (idempotency) ==")
    res = comtrade_client.fetch_trade_data(
        reporter=config.TURKEY_CODE, partner=config.CHINA_CODE, year=2020,
        flow=config.EXPORT_FLOW, commodity=commodity, commodity_desc=desc,
    )
    stats = database.upsert_records(conn, res)
    print("re-ingest stats:", stats)
    assert stats["inserted"] == 0, "re-ingest must not insert duplicates"
    assert stats["skipped"] == 1

    print("\n== Query + analysis (TR->CN) ==")
    series_raw = database.fetch_direction_series(conn, "TR_TO_CN", commodity, config.DEFAULT_YEAR_MIN, config.DEFAULT_YEAR_MAX)
    series = analysis.annual_series(series_raw)
    yoy = analysis.yoy_changes(series)
    metrics = analysis.summary_metrics(series)
    print("years:", [s["year"] for s in series])
    print("latest:", analysis.format_usd(metrics["latest_value"]), "CAGR:", metrics["cagr"])
    print("first 3 YOY:", [(y["year"], y["pct"], y["status"]) for y in yoy[:3]])
    assert len(series) == n_years
    assert metrics["latest_value"] > 0

    print("\n== SQL queries ==")
    totals = database.sql_annual_totals(
        conn, config.TURKEY_CODE, config.CHINA_CODE, config.EXPORT_FLOW, commodity, config.DEFAULT_YEAR_MIN, config.DEFAULT_YEAR_MAX
    )
    syoy = database.sql_yoy(
        conn, config.TURKEY_CODE, config.CHINA_CODE, config.EXPORT_FLOW, commodity, config.DEFAULT_YEAR_MIN, config.DEFAULT_YEAR_MAX
    )
    print("SQL totals rows:", len(totals), "| SQL yoy rows:", len(syoy))
    assert len(totals) == n_years

    print("\n== Charts ==")
    f1 = charts.annual_value_line(series, "test", "TR->CN", "FOB")
    f2 = charts.yoy_bar(yoy, "test")
    other = analysis.annual_series(
        database.fetch_direction_series(conn, "CN_TO_TR", commodity, config.DEFAULT_YEAR_MIN, config.DEFAULT_YEAR_MAX)
    )
    rows = analysis.compare_directions(series, other)
    f3 = charts.direction_comparison(rows, "TR->CN", "CN->TR")
    f4 = charts.balance_chart(rows, "TR->CN", "CN->TR")
    for name, fig in (("line", f1), ("yoy", f2), ("compare", f3), ("balance", f4)):
        assert len(fig.data) >= 1, f"{name} chart has no traces"
        print(f"  {name}: {len(fig.data)} trace(s) OK")

    print("\n== Validation ==")
    issues = database.validate(conn)
    for i in issues:
        print(f"  [{i['level']}] {i['check']}: {i['count']} — {i['message']}")
    errors = [i for i in issues if i["level"] == "error" and i["count"] > 0]
    assert not errors, f"validation errors: {errors}"

    print("\n== Mode isolation (sample rows must never leak into real reads) ==")
    os.environ["USE_SAMPLE_DATA"] = "0"
    try:
        leaked = database.fetch_direction_series(conn, "TR_TO_CN", commodity, config.DEFAULT_YEAR_MIN, config.DEFAULT_YEAR_MAX)
        print("real-mode rows visible in a sample-only DB:", len(leaked))
        assert leaked == [], "sample rows leaked into real-mode reads"
        print("  isolation OK — a fallback can never be mixed into a real series")
    finally:
        os.environ["USE_SAMPLE_DATA"] = "1"

    conn.close()
    print("\nALL CHECKS PASSED ✅")


if __name__ == "__main__":
    main()
