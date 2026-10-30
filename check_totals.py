
import os
import requests
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("COMTRADE_API_KEY")

url = "https://comtradeapi.un.org/data/v1/get/C/A/HS"

directions = [
    {"name": "China -> Türkiye", "reporter": 156, "partner": 792},
    {"name": "Türkiye -> China", "reporter": 792, "partner": 156},
]

headers = {"Ocp-Apim-Subscription-Key": api_key}

for direction in directions:
    params = {
        "reporterCode": direction["reporter"],
        "partnerCode": direction["partner"],
        "period": 2023,
        "flowCode": "X",
        "cmdCode": "TOTAL",
        "breakdownMode": "classic",
        "maxRecords": 10,
    }

    response = requests.get(
        url,
        params=params,
        headers=headers,
        timeout=60,
    )
    response.raise_for_status()

    records = response.json().get("data", [])

    print("\nDirection:", direction["name"])
    print("Records:", len(records))

    for record in records:
        print("Value:", record.get("primaryValue"))
        print("Reported:", record.get("isReported"))
        print("Aggregate:", record.get("isAggregate"))
