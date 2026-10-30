
import os
import json
from pathlib import Path

import psycopg
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
DATA_DIR = Path(__file__).parent

if not DATABASE_URL:
    raise ValueError("DATABASE_URL .env dosyasinda bulunamadi.")

# Find all 14 yearly Classic data files.
files = sorted(DATA_DIR.glob("*_classic_20*.json"))

if len(files) != 14:
    raise RuntimeError(
        f"14 Classic dosyasi bekleniyordu, {len(files)} bulundu. "
        "Aktarim durduruldu."
    )

country_map = {
    156: "CHN",
    792: "TUR",
}

rows_by_key = {}
skipped_total = 0
skipped_missing = 0
duplicate_in_files = 0

# Read and prepare all files before writing to the database.
for path in files:
    with path.open("r", encoding="utf-8") as file:
        content = json.load(file)

    records = content.get("data", [])

    if not isinstance(records, list):
        raise ValueError(f"Beklenmeyen JSON yapisi: {path.name}")

    for row in records:
        hs_code = row.get("cmdCode")
        value = row.get("primaryValue")
        year_value = row.get("refYear") or row.get("period")

        # TOTAL is an overall total, not a product code.
        if hs_code == "TOTAL":
            skipped_total += 1
            continue

        if hs_code is None or value is None or year_value is None:
            skipped_missing += 1
            continue

        reporter = country_map.get(int(row["reporterCode"]))
        partner = country_map.get(int(row["partnerCode"]))

        if reporter is None or partner is None or reporter == partner:
            raise ValueError(
                f"Beklenmeyen ulke kodlari: {path.name}, {hs_code}"
            )

        flow = str(row.get("flowCode") or "X")
        year = int(year_value)
        hs_code = str(hs_code)

        # Match the existing database unique constraint.
        key = (reporter, partner, flow, year, hs_code)

        if key in rows_by_key:
            duplicate_in_files += 1
            continue

        partner2_code = row.get("partner2Code")
        partner2_iso = country_map.get(int(partner2_code)) if partner2_code else None

        mot_code = row.get("motCode")
        estimation_flag = row.get("legacyEstimationFlag")

        rows_by_key[key] = (
            reporter,
            partner,
            flow,
            year,
            hs_code,
            value,
            "USD",
            "FOB" if row.get("fobvalue") is not None else None,
            row.get("isReported"),
            "UN Comtrade API",
            row.get("classificationCode"),
            row.get("customsCode"),
            int(mot_code) if mot_code is not None else None,
            partner2_iso,
            row.get("isAggregate"),
            int(estimation_flag) if estimation_flag is not None else None,
        )

print(f"Classic files found: {len(files)}")
print(f"Unique records prepared: {len(rows_by_key)}")
print(f"TOTAL records skipped: {skipped_total}")
print(f"Records missing required data: {skipped_missing}")
print(f"Duplicate keys in files skipped: {duplicate_in_files}")

# Write the prepared records in one database transaction.
insert_sql = """
    INSERT INTO trade_records (
        reporter_code,
        partner_code,
        flow_code,
        year,
        hs_code,
        trade_value_usd,
        currency_code,
        valuation_basis,
        is_reported,
        source_name,
        classification_code,
        customs_code,
        mot_code,
        partner2_iso,
        is_aggregate,
        legacy_estimation_flag
        )
    VALUES (
    %s, %s, %s, %s, %s, %s, %s, %s,
    %s, %s, %s, %s, %s, %s, %s, %s
    )
    ON CONFLICT (
        reporter_code, partner_code, flow_code, year, hs_code
    ) DO NOTHING;
"""

with psycopg.connect(DATABASE_URL) as conn:
    with conn.cursor() as cur:
        # Preserve the estimation flag for future analysis.
        cur.execute("""
            ALTER TABLE trade_records
            ADD COLUMN IF NOT EXISTS legacy_estimation_flag integer;
        """)

        # Ensure the sequence is not behind the existing IDs.
        cur.execute("""
            SELECT setval(
                'public.trade_records_id_seq',
                GREATEST(
                    COALESCE((SELECT MAX(id) FROM trade_records), 1),
                    (SELECT last_value FROM public.trade_records_id_seq)
                ),
                true
            );
        """)

        cur.executemany(insert_sql, rows_by_key.values())

        cur.execute("SELECT COUNT(*) FROM trade_records;")
        final_count = cur.fetchone()[0]

        cur.execute("""
            SELECT reporter_code, partner_code, year, COUNT(*)
            FROM trade_records
            GROUP BY reporter_code, partner_code, year
            ORDER BY year, reporter_code;
        """)
        summary = cur.fetchall()

print("\n=== IMPORT COMPLETED ===")
print(f"Total records now in Neon: {final_count}")
print("\nRecords by direction and year:")

for reporter, partner, year, count in summary:
    print(f"{year}: {reporter} -> {partner}: {count}")