"""
dataset_report.py — Coverage report for the project's own database.

Prints what the database actually contains: how many HS chapters, which years,
which direction, how many observations, and where the gaps are. Use it for the
team write-up (and to prove the dataset is complete rather than sampled).

Usage:
    python dataset_report.py
    python dataset_report.py --csv data/coverage.csv
"""

from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path

import analysis
import config
import database


def human_bytes(n: int) -> str:
    size = float(n)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024 or unit == "GB":
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} GB"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default="", help="also write the coverage table to this CSV")
    ap.add_argument(
        "--export-catalogue", action="store_true",
        help="merge every HS code found in the database into hs_catalogue.json "
             "so it becomes searchable by name in the app",
    )
    args = ap.parse_args()

    db_path = Path(config.DB_PATH)
    if not db_path.exists():
        print(f"No database at {db_path}. Run build_dataset.py first.")
        return

    conn = database.get_connection()
    database.init_db(conn)
    flag = database.sample_flag()

    counts = database.counts(conn)
    chapters = conn.execute(
        f"""SELECT commodity_code, COUNT(*) n, MIN(year), MAX(year)
            FROM trade_records WHERE is_total=1 AND is_sample={flag}
            GROUP BY commodity_code ORDER BY commodity_code"""
    ).fetchall()

    years = [r[0] for r in conn.execute(
        f"""SELECT DISTINCT year FROM trade_records
            WHERE is_total=1 AND is_sample={flag} ORDER BY year"""
    ).fetchall()]

    print("=" * 78)
    print("DATASET REPORT — Türkiye <-> China trade")
    print("=" * 78)
    print(f"database      : {db_path}  ({human_bytes(db_path.stat().st_size)})")
    print(f"data mode     : {config.data_mode()}")
    print(f"total rows    : {counts['total_rows']} (analysis table, one per product/direction/year)")
    print(f"raw rows      : {counts['raw_rows']} (audit archive, includes breakdowns)")
    print(f"ingestions    : {counts['ingest_logs']}")
    print(f"HS codes      : {len(chapters)} with data")
    print(f"years         : {years}")

    # Per-year coverage: how many (product, direction) observations exist.
    print("\n--- observations per year ---")
    for y in years:
        n = conn.execute(
            f"""SELECT COUNT(*) FROM trade_records
                WHERE is_total=1 AND is_sample={flag} AND year=?""", (y,)
        ).fetchone()[0]
        print(f"  {y}: {n:>4} observations")

    # Direction totals.
    print("\n--- by direction ---")
    for key, d in config.DIRECTIONS.items():
        row = conn.execute(
            f"""SELECT COUNT(*) n, SUM(trade_value) v FROM trade_records
                WHERE is_total=1 AND is_sample={flag}
                  AND reporter_code=? AND partner_code=? AND flow_code=?""",
            (d["reporter_code"], d["partner_code"], d["flow_code"]),
        ).fetchone()
        total = analysis.format_usd(row["v"] or 0)
        print(f"  {d['label']:<18} {row['n']:>4} observations, cumulative {total}")

    # Prefer the API's own description (stored with each row); fall back to the
    # curated catalogue for codes it covers.
    desc_map = {
        r[0]: (r[1] or "")
        for r in conn.execute(
            f"""SELECT commodity_code, MAX(commodity_desc) FROM trade_records
                WHERE is_total=1 AND is_sample={flag} GROUP BY commodity_code"""
        ).fetchall()
    }

    # Chapters that exist in the catalogue but have no data at all.
    catalogue = {c["code"] for c in config.load_hs_catalogue()}
    have = {r["commodity_code"] for r in chapters}
    missing = sorted(c for c in catalogue if c not in have)
    if missing:
        print(f"\ncatalogue codes with no data in range: {missing}")

    # Gaps: chapters where a direction has fewer years than the range.
    print("\n--- coverage table (years with data per direction) ---")
    print(f"{'HS':<6}{'TR->CN':<10}{'CN->TR':<10}{'name'}")
    rows_for_csv = []
    for r in chapters:
        code = r["commodity_code"]
        per = {}
        for key, d in config.DIRECTIONS.items():
            per[key] = conn.execute(
                f"""SELECT COUNT(DISTINCT year) FROM trade_records
                    WHERE is_total=1 AND is_sample={flag} AND commodity_code=?
                      AND reporter_code=? AND partner_code=? AND flow_code=?""",
                (code, d["reporter_code"], d["partner_code"], d["flow_code"]),
            ).fetchone()[0]
        name = (config.get_hs_entry(code) or {}).get("name", "") or desc_map.get(code, "")
        print(f"{code:<6}{per['TR_TO_CN']:<10}{per['CN_TO_TR']:<10}{name[:46]}")
        rows_for_csv.append({
            "hs_code": code, "name": name,
            "tr_to_cn_years": per["TR_TO_CN"], "cn_to_tr_years": per["CN_TO_TR"],
            "total_years_in_range": len(years),
        })

    issues = database.validate(conn)
    print("\n--- data quality ---")
    for i in issues:
        print(f"  [{i['level']:<7}] {i['check']:<22} {i['count']:>6}  {i['message']}")
    conn.close()

    if args.csv:
        import csv
        out = Path(args.csv)
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=list(rows_for_csv[0].keys()))
            writer.writeheader()
            writer.writerows(rows_for_csv)
        print(f"\ncoverage CSV written to {out}")

    if args.export_catalogue:
        import json
        path = Path(config.HS_CATALOGUE_PATH)
        existing = []
        if path.exists():
            try:
                existing = json.loads(path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                existing = []
        known = {c["code"] for c in existing}
        added = 0
        for code, desc in sorted(desc_map.items()):
            if code in known or not desc:
                continue
            existing.append({
                "code": code,
                "name": desc,
                "category": "HS chapter (from dataset)" if len(code) == 2 else "HS code (from dataset)",
            })
            added += 1
        existing.sort(key=lambda c: (len(c["code"]), c["code"]))
        path.write_text(json.dumps(existing, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\ncatalogue updated: {added} new code(s) added, {len(existing)} total -> {path}")


if __name__ == "__main__":
    main()
