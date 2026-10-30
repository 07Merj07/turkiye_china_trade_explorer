
import os
from pathlib import Path

import pandas as pd
import psycopg
from dotenv import load_dotenv

# Load database credentials from the .env file
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL was not found in the .env file.")

# Locate the Excel catalogue in the project folder
BASE_DIR = Path(__file__).resolve().parent
EXCEL_FILE = BASE_DIR / "HS2022_Product_Catalog_Cleaned.xlsx"

if not EXCEL_FILE.exists():
    raise FileNotFoundError(f"Catalogue file not found: {EXCEL_FILE}")

# Read product codes as text to preserve leading zeros
df = pd.read_excel(
    EXCEL_FILE,
    dtype={
        "id": str,
        "parent": str,
        "text": str,
        "standardUnitAbbr": str,
    },
)

# Remove rows without a product code or description
df = df.dropna(subset=["id", "text"])
df["id"] = df["id"].str.strip()
df["text"] = df["text"].str.strip()

# Exclude the general TOTAL row
df = df[df["id"].str.upper() != "TOTAL"]

# Convert catalogue fields to the database format
rows = []
for _, row in df.iterrows():
    code = row["id"]
    description = row["text"]

    parent = row.get("parent")
    parent = None if pd.isna(parent) or not str(parent).strip() else str(parent).strip()

    is_leaf = row.get("isLeaf")
    is_leaf = None if pd.isna(is_leaf) else bool(is_leaf)

    level = row.get("aggrlevel")
    level = None if pd.isna(level) else int(level)

    unit = row.get("standardUnitAbbr")
    unit = None if pd.isna(unit) or not str(unit).strip() else str(unit).strip()

    rows.append((
        code,
        "HS2022",
        description,
        parent,
        is_leaf,
        level,
        unit,
        "HS2022 Product Catalog",
    ))

# Import the catalogue into Neon
with psycopg.connect(DATABASE_URL) as conn:
    with conn.cursor() as cur:
        cur.executemany(
            """
            INSERT INTO products (
                hs_code,
                hs_version,
                official_description_en,
                parent_hs_code,
                is_leaf,
                aggregation_level,
                standard_unit_abbr,
                source_name
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT DO NOTHING
            """,
            rows,
        )

        cur.execute("SELECT COUNT(*) FROM products")
        total = cur.fetchone()[0]

print(f"Catalogue rows prepared: {len(rows)}")
print(f"Total rows now in products: {total}")
