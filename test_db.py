
import os
import psycopg
from dotenv import load_dotenv

# Load database connection settings.
load_dotenv()
database_url = os.getenv("DATABASE_URL")

# Retrieve trade data from the database.
with psycopg.connect(database_url) as connection:
    with connection.cursor() as cursor:
        
        cursor.execute("""
            SELECT
                reporter_code,
                partner_code,
                year,
                hs_code,
                trade_value_usd
                FROM trade_records
                WHERE reporter_code = 'TUR'
                AND partner_code = 'CHN'
                AND flow_code = 'X'
                AND year = 2023;
        """)

        rows = cursor.fetchall()

        for row in rows:
            print(row)
