
import json
import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv


# Load database connection settings.
load_dotenv()
database_url = os.getenv("DATABASE_URL")

if not database_url:
    raise ValueError("DATABASE_URL bulunamadi!")

# Read the saved live API response.
file_path = Path("turkey_to_china_response.json")

with file_path.open("r", encoding="utf-8") as file:
    response = json.load(file)

records = response.get("data", [])

if len(records) != 1:
    raise ValueError(
        f"Expected exactly one record; received {len(records)}. "
        "Import stopped to avoid saving an unverified result."
    )

record = records[0]

# Validate required source fields.
required_fields = [
    "reporterCode",
    "partnerCode",
    "flowCode",
    "refYear",
    "cmdCode",
    "primaryValue",
]

missing_fields = [
    field for field in required_fields
    if record.get(field) is None
]

if missing_fields:
    raise ValueError(f"Missing required fields: {missing_fields}")

# Convert country codes to the codes used by our database.
country_codes = {
    792: "TUR",
    156: "CHN",
}

reporter_code = country_codes.get(record["reporterCode"])
partner_code = country_codes.get(record["partnerCode"])

if not reporter_code or not partner_code:
    raise ValueError("Unexpected country code; import stopped.")

if {reporter_code, partner_code} != {"TUR", "CHN"}:
    raise ValueError("This project only supports Türkiye and China.")

# Prepare the database values.
values = (
    reporter_code,
    partner_code,
    record["flowCode"],
    int(record["refYear"]),
    str(record["cmdCode"]),
    record["primaryValue"],
    "USD",
    "FOB" if record.get("fobvalue") is not None else None,
    record.get("isReported"),
    "UN Comtrade",
    record.get("classificationCode"),
    record.get("customsCode"),
    record.get("motCode"),
    record.get("partner2ISO"),
    record.get("isAggregate"),
)

# Insert only if the existing unique key is not present.
# Check whether the database generates IDs automatically.
with psycopg.connect(database_url) as connection:
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT column_default, is_identity
            FROM information_schema.columns
            WHERE table_name = 'trade_records'
              AND column_name = 'id';
        """)

        id_settings = cursor.fetchone()

        print("ID default:", id_settings[0])
        print("ID identity:", id_settings[1])
with psycopg.connect(database_url) as connection:
    with connection.cursor() as cursor:
        cursor.execute("""
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
                is_aggregate
            )
            VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s
            )
            ON CONFLICT (
                reporter_code,
                partner_code,
                flow_code,
                year,
                hs_code
            ) DO NOTHING
            RETURNING id;
        """, values)

        inserted = cursor.fetchone()

        if inserted:
            print("Trade record inserted. ID:", inserted[0])
        else:
            print("Matching record already exists; nothing inserted.")

print("Import operation finished.")
