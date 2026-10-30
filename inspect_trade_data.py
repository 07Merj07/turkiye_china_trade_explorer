
import json
from pathlib import Path
from collections import Counter

files = sorted(Path(".").glob("*_to_*_20*.json"))

for file_path in files:
    with file_path.open("r", encoding="utf-8") as file:
        response = json.load(file)

    records = response.get("data", [])

    # Count distinct product codes and reporting flags.
    products = {
        str(record.get("cmdCode"))
        for record in records
        if record.get("cmdCode") is not None
    }

    aggregate_counts = Counter(
        str(record.get("isAggregate"))
        for record in records
    )

    reported_counts = Counter(
        str(record.get("isReported"))
        for record in records
    )

    # Check whether the database's current unique key repeats.
    keys = [
        (
            record.get("reporterCode"),
            record.get("partnerCode"),
            record.get("flowCode"),
            record.get("refYear"),
            str(record.get("cmdCode")),
        )
        for record in records
    ]

    duplicate_count = len(keys) - len(set(keys))

    print(f"\nFile: {file_path.name}")
    print("Records:", len(records))
    print("Distinct product codes:", len(products))
    print("Repeated database keys:", duplicate_count)
    print("Aggregate flags:", dict(aggregate_counts))
    print("Reported flags:", dict(reported_counts))

print("\nInspection finished.")

import json
from pathlib import Path
from collections import Counter

with Path("turkey_to_china_2023.json").open(
    "r", encoding="utf-8"
) as file:
    records = json.load(file)["data"]

counts = Counter(str(r.get("cmdCode")) for r in records)
repeated_code = next(code for code, count in counts.items() if count > 1)

print("İncelediğimiz ürün kodu:", repeated_code)

for record in records:
    if str(record.get("cmdCode")) == repeated_code:
        print({
            "product": record.get("cmdCode"),
            "value": record.get("primaryValue"),
            "aggregate": record.get("isAggregate"),
            "reported": record.get("isReported"),
            "customs": record.get("customsCode"),
            "transport": record.get("motCode"),
            "partner2": record.get("partner2Code"),
            "classification": record.get("classificationCode"),
        })
