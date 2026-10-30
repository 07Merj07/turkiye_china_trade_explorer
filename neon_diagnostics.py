
import os
import psycopg
from dotenv import load_dotenv

load_dotenv()

with psycopg.connect(os.getenv("DATABASE_URL")) as conn:
    with conn.cursor() as cur:

        print("\n--- CLASSIFICATIONS ---")
        cur.execute("""
            SELECT classification_code, COUNT(*)
            FROM trade_records
            GROUP BY classification_code
            ORDER BY classification_code;
        """)
        for row in cur.fetchall():
            print(row)

        print("\n--- AGGREGATE FLAGS ---")
        cur.execute("""
            SELECT reporter_code, is_aggregate, COUNT(*)
            FROM trade_records
            GROUP BY reporter_code, is_aggregate
            ORDER BY reporter_code, is_aggregate;
        """)
        for row in cur.fetchall():
            print(row)

        print("\n--- SAMPLE PRODUCT: 610910 ---")
        cur.execute("""
            SELECT
                reporter_code,
                year,
                classification_code,
                hs_code,
                COUNT(*) AS record_count,
                COUNT(DISTINCT trade_value_usd) AS distinct_values
            FROM trade_records
            WHERE hs_code = '610910'
            GROUP BY
                reporter_code, year, classification_code, hs_code
            ORDER BY year, reporter_code;
        """)
        for row in cur.fetchall():
            print(row)
