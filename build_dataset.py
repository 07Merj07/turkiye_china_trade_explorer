"""
build_dataset.py — Build the project's own complete trade database.

Loads every HS 2-digit chapter for Türkiye <-> China, for a year range, in both
directions, into the SQLite database shipped with the app. The result is a
self-contained dataset: the app answers from it without touching the API.

The build is RESUMABLE. Every attempt is recorded in `fetch_attempts`, so an
interrupted run continues where it stopped, and years that legitimately have no
data are never re-queried (that is where most of the wasted API calls would go).

Usage:
    python build_dataset.py                      # chapters 01-97, 2018-2025
    python build_dataset.py --years 2018-2025
    python build_dataset.py --chapters 84,85,94
    python build_dataset.py --force              # re-query everything
"""

from __future__ import annotations

import argparse
import sys
import time

import comtrade_client
import config
import database

# HS chapters 01-97; chapter 77 is reserved by the HS convention and has no data.
CHAPTERS = [f"{i:02d}" for i in range(1, 98) if i != 77]


def parse_years(text: str) -> tuple[int, int]:
    if "-" in text:
        a, b = text.split("-", 1)
        return int(a), int(b)
    y = int(text)
    return y, y


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--years", default=f"2018-{config.DEFAULT_YEAR_MAX}")
    ap.add_argument("--chapters", default="", help="comma-separated HS chapters")
    ap.add_argument("--directions", default="TR_TO_CN,CN_TO_TR")
    ap.add_argument("--force", action="store_true", help="re-query years already attempted")
    args = ap.parse_args()

    year_min, year_max = parse_years(args.years)
    years = list(range(year_min, year_max + 1))
    chapters = (
        [c.strip().zfill(2) for c in args.chapters.split(",") if c.strip()]
        if args.chapters else CHAPTERS
    )
    directions = [d.strip() for d in args.directions.split(",") if d.strip()]

    mode = config.data_mode()
    if mode == "sample":
        print("Refusing to build the dataset in sample mode (would store fake data).")
        return 2

    total_requests = len(chapters) * len(years) * len(directions)
    print(
        f"mode={mode}  chapters={len(chapters)}  years={year_min}-{year_max} "
        f"directions={len(directions)}  max_requests={total_requests}",
        flush=True,
    )

    conn = database.get_connection()
    database.init_db(conn)

    started = time.time()
    done = skipped = empty = failed = new_rows = 0

    for ci, commodity in enumerate(chapters, start=1):
        desc = (config.get_hs_entry(commodity) or {}).get("name", "")
        for direction_key in directions:
            d = config.direction_meta(direction_key)
            skip = set()
            if not args.force:
                skip = database.cached_years(conn, direction_key, commodity, year_min, year_max)
                skip |= database.attempted_years(conn, direction_key, commodity, year_min, year_max)

            got = 0
            for year in years:
                if year in skip:
                    skipped += 1
                    continue
                res = comtrade_client.fetch_trade_data(
                    reporter=d["reporter_code"], partner=d["partner_code"],
                    year=year, flow=d["flow_code"], commodity=commodity,
                    commodity_desc=desc,
                )
                stats = database.upsert_records(conn, res)
                done += 1
                new_rows += stats["inserted"]
                if res.status == "empty":
                    empty += 1
                elif res.status == "fallback":
                    failed += 1
                    print(f"  ! fallback {commodity} {direction_key} {year}: {res.live_error[:90]}",
                          flush=True)
                if stats["totals"]:
                    got += 1

            elapsed = time.time() - started
            rate = done / elapsed * 60 if elapsed > 0 and done else 0.0
            remaining = (total_requests - done - skipped) / max(rate, 0.01)
            print(
                f"[{ci}/{len(chapters)}] HS {commodity} {direction_key:<8} "
                f"with-data {got}/{len(years)}  |  done {done}  skip {skipped}  "
                f"empty {empty}  fail {failed}  new {new_rows}  "
                f"| {rate:.1f} req/min  ~{remaining:.0f} min left",
                flush=True,
            )

    issues = database.validate(conn)
    cts = database.counts(conn)
    coverage = conn.execute(
        """SELECT COUNT(DISTINCT commodity_code) FROM trade_records
           WHERE is_total=1 AND is_sample=0"""
    ).fetchone()[0]
    conn.close()

    print("\n=== build summary ===")
    print(f"requests made : {done}")
    print(f"years skipped : {skipped} (already stored or confirmed empty)")
    print(f"empty results : {empty}")
    print(f"fallbacks     : {failed}")
    print(f"new total rows: {new_rows}")
    print(f"elapsed       : {(time.time() - started) / 60:.1f} min")
    print(f"counts        : {cts}")
    print(f"HS codes with data: {coverage}")
    for i in issues:
        print(f"  [{i['level']}] {i['check']}: {i['count']} — {i['message']}")

    errors = [i for i in issues if i["level"] == "error" and i["count"] > 0]
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
