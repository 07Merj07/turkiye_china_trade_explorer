
import os
import psycopg
import pandas as pd
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")


def get_product_trade(hs_code, start_year=2019, end_year=2025):
    """Fetch annual trade records for a selected product."""

    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    year,
                    reporter_code,
                    partner_code,
                    trade_value_usd
                FROM trade_records
                WHERE hs_code = %s
                  AND year BETWEEN %s AND %s
                ORDER BY year, reporter_code;
                """,
                (hs_code, start_year, end_year)
            )
            rows = cur.fetchall()

    return pd.DataFrame(
        rows,
        columns=[
            "year",
            "reporter_code",
            "partner_code",
            "trade_value_usd"
        ]
    )


# Fetch trade data for cotton T-shirts
df = get_product_trade("610910")

# Calculate year-over-year changes separately for each reporter
df["previous_year_value"] = (
    df.groupby("reporter_code")["trade_value_usd"].shift(1)
)

df["yoy_change_percent"] = (
    (df["trade_value_usd"] - df["previous_year_value"])
    / df["previous_year_value"]
    * 100
).round(2)

print(df.to_string(index=False))
