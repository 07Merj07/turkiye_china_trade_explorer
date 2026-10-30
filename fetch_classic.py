
import json
import os
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("COMTRADE_API_KEY")

if not api_key:
    raise ValueError("COMTRADE_API_KEY bulunamadi!")

url = "https://comtradeapi.un.org/data/v1/get/C/A/HS"
headers = {"Ocp-Apim-Subscription-Key": api_key}

directions = [
    {"name": "china_to_turkey", "reporter": 156, "partner": 792},
    {"name": "turkey_to_china", "reporter": 792, "partner": 156},
]

for direction in directions:
    for year in range(2019, 2026):
        params = {
            "reporterCode": direction["reporter"],
            "partnerCode": direction["partner"],
            "period": year,
            "flowCode": "X",
            "breakdownMode": "classic",
            "maxRecords": 100000,
        }

        print(f"Fetching {direction['name']} - {year}")

        response = requests.get(
            url,
            params=params,
            headers=headers,
            timeout=120,
        )
        response.raise_for_status()

        result = response.json()
        records = result.get("data", [])

        if not records:
            print("WARNING: No records returned.")

        output_path = Path(
            f"{direction['name']}_classic_{year}.json"
        )

        with output_path.open("w", encoding="utf-8") as file:
            json.dump(result, file, ensure_ascii=False, indent=2)

        print("Records:", len(records))
        print("Saved:", output_path)

        time.sleep(1.1)

print("All Classic downloads finished.")
