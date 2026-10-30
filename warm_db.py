"""
warm_db.py — Pre-fetch real UN Comtrade data into the local SQLite database.

The UI serves any year already stored in the database without calling the API,
so a warmed database makes the deployed app open instantly for visitors and
keeps API usage (and rate-limit risk) low.

Usage:
    python warm_db.py                # default product list, both directions
    python warm_db.py 94 9405 61     # only these HS codes
    python warm_db.py --years 2018-2025 94
"""

from __future__ import annotations

import argparse
import sys
import time

import comtrade_client
import config
import database

# Products worth pre-fetching: the catalogue's most likely selections.
DEFAULT_PRODUCTS = ["94", "9405", "61", "85", "84"]


def parse_years(text: str) -> tuple[int, int]:
    if "-" in text:
        a, b = text.split("-", 1)
        return int(a), int(b)
    y = int(text)
    return y, y


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("products", nargs="*", help="HS codes (default: a common set)")
    ap.add_argument("--years", default=f"2018-{config.DEFAULT_YEAR_MAX}")
    ap.add_argument("--both", action="store_true", default=True)
    args = ap.parse_args()

    products = args.products or DEFAULT_PRODUCTS
    year_min, year_max = parse_years(args.years)
    years = list(range(year_min, year_max + 1))

    print(f"mode: {config.data_mode()}  |  years: {year_min}-{year_max}  |  products: {products}")
    if config.data_mode() == "sample":
        print("Refusing to warm the database in sample mode (would store fake data).")
        return 2

    conn = database.get_connection()
    database.init_db(conn)

    started = time.time()
    total = 0
    failures = 0

    for commodity in products:
        desc = (config.get_hs_entry(commodity) or {}).get("name", "")
        for direction_key in ("TR_TO_CN", "CN_TO_TR"):
            d = config.direction_meta(direction_key)
            for year in years:
                res = comtrade_client.fetch_trade_data(
                    reporter=d["reporter_code"], partner=d["partner_code"],
                    year=year, flow=d["flow_code"], commodity=commodity,
                    commodity_desc=desc,
                )
                stats = database.upsert_records(conn, res)
                total += 1
                if res.status == "fallback":
                    failures += 1
                flag = "NEW" if stats["inserted"] else "have"
                value = next(
                    (r["trade_value"] for r in res.records if r["is_total"] == 1), None
                )
                shown = f"{value:,.0f}" if value is not None else "—"
                print(
                    f"  {commodity:>5} {direction_key:<8} {year}  {res.status:<8} "
                    f"{flag:<4} {shown:>15}  ({stats['totals']} total / {stats['breakdowns']} bd)"
                )

    series = database.fetch_direction_series(conn, "TR_TO_CN", products[0], year_min, year_max)
    issues = database.validate(conn)
    cts = database.counts(conn)
    conn.close()

    print(f"\ndone: {total} requests, {failures} fallbacks, {time.time() - started:.0f}s")
    print("counts:", cts)
    print(f"spot check TR->CN {products[0]}:",
          [(s["year"], s["trade_value"]) for s in series])
    errors = [i for i in issues if i["level"] == "error" and i["count"] > 0]
    print("validation errors:", errors or "none")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
