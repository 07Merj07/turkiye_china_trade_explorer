
import os

import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv

load_dotenv()


def get_connection():
    """Connect to the Neon PostgreSQL database."""
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        raise RuntimeError("DATABASE_URL is missing from .env")

    return psycopg.connect(database_url, row_factory=dict_row)


def search_products(query="", limit=50):
    """Search products by HS code or English description."""

    query = query.strip()

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    hs_code AS code,
                    official_description_en AS name,
                    hs_version,
                    parent_hs_code,
                    is_leaf,
                    aggregation_level
                FROM products
                WHERE hs_code ILIKE %s
                   OR official_description_en ILIKE %s
                ORDER BY
                    CASE WHEN hs_code = %s THEN 0 ELSE 1 END,
                    is_leaf DESC,
                    aggregation_level DESC,
                    hs_code
                LIMIT %s;
                """,
                (
                    f"%{query}%",
                    f"%{query}%",
                    query,
                    limit
                )
            )

            return cur.fetchall()


def fetch_direction_series(direction_key, commodity, year_min, year_max):
    """Fetch annual export values for one trade direction."""

    directions = {
        "TR_TO_CN": ("TUR", "CHN"),
        "CN_TO_TR": ("CHN", "TUR"),
    }

    if direction_key not in directions:
        raise ValueError(f"Unknown direction: {direction_key}")

    reporter, partner = directions[direction_key]

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    year,
                    COUNT(*) AS record_count,
                    COUNT(DISTINCT trade_value_usd) AS distinct_values,
                    MAX(trade_value_usd) AS trade_value
                FROM trade_records
                WHERE reporter_code = %s
                  AND partner_code = %s
                  AND flow_code = 'X'
                  AND hs_code = %s
                  AND year BETWEEN %s AND %s
                  AND classification_code =
                      CASE
                          WHEN year BETWEEN 2019 AND 2021 THEN 'H5'
                          WHEN year BETWEEN 2022 AND 2025 THEN 'H6'
                      END
                  AND currency_code = 'USD'
                  AND valuation_basis = 'FOB'
                GROUP BY year
                ORDER BY year;
                """,
                (reporter, partner, commodity, year_min, year_max)
            )

            rows = cur.fetchall()

    duplicates = [
        row for row in rows
        if row["record_count"] > 1
    ]

    if duplicates:
        details = [
            f"{row['year']}: {row['record_count']} records"
            for row in duplicates
        ]
        raise ValueError(
            "Multiple records found for the same product and year: "
            + ", ".join(details)
        )

    return [
        {
            "year": row["year"],
            "trade_value": float(row["trade_value"])
        }
        for row in rows
    ]
