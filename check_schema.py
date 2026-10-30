
import os
import psycopg
from dotenv import load_dotenv

load_dotenv()

with psycopg.connect(os.getenv("DATABASE_URL")) as conn:
    with conn.cursor() as cur:
        cur.execute("""
            SELECT table_name, column_name, data_type
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name IN ('trade_records', 'products')
            ORDER BY table_name, ordinal_position;
        """)

        for row in cur.fetchall():
            print(" | ".join(row))
