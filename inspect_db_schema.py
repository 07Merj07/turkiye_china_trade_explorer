
import os
import psycopg
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL .env dosyasinda bulunamadi.")

with psycopg.connect(DATABASE_URL) as conn:
    with conn.cursor() as cur:

        # 1. Show the columns and data types of trade_records.
        cur.execute("""
            SELECT
                column_name,
                data_type,
                is_nullable,
                column_default
            FROM information_schema.columns
            WHERE table_name = 'trade_records'
            ORDER BY ordinal_position;
        """)

        print("\n=== TABLE COLUMNS ===")
        for row in cur.fetchall():
            print(row)

        # 2. Show constraints, such as primary keys and unique rules.
        cur.execute("""
            SELECT
                conname,
                pg_get_constraintdef(oid)
            FROM pg_constraint
            WHERE conrelid = 'trade_records'::regclass
            ORDER BY conname;
        """)

        print("\n=== TABLE CONSTRAINTS ===")
        for row in cur.fetchall():
            print(row)

        # 3. Count the records already stored in the table.
        cur.execute("SELECT COUNT(*) FROM trade_records;")
        print("\nExisting trade_records:", cur.fetchone()[0])

print("\nSchema inspection completed.")

with psycopg.connect(DATABASE_URL) as conn:
    with conn.cursor() as cur:
        cur.execute("""
            SELECT id, reporter_code, partner_code, year, hs_code
            FROM trade_records
            ORDER BY id;
        """)

        print("\n=== EXISTING RECORD IDS ===")
        for row in cur.fetchall():
            print(row)

        cur.execute("""
            SELECT pg_get_serial_sequence('trade_records', 'id');
        """)

        print("\nID sequence:", cur.fetchone()[0])
        
with psycopg.connect(DATABASE_URL) as conn:
    with conn.cursor() as cur:
        cur.execute("""
            SELECT column_default
            FROM information_schema.columns
            WHERE table_name = 'trade_records'
              AND column_name = 'id';
        """)
        print("ID default:", cur.fetchone()[0])

        cur.execute("""
            SELECT last_value, is_called
            FROM public.trade_records_id_seq;
        """)
        print("ID sequence status:", cur.fetchone())
