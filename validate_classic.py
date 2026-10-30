
import json
from pathlib import Path
from collections import Counter

files = [
    Path("china_to_turkey_classic_2023.json"),
    Path("turkey_to_china_classic_2023.json"),
]

for file_path in files:
    with file_path.open("r", encoding="utf-8") as file:
        records = json.load(file)["data"]

    product_codes = [str(r.get("cmdCode")) for r in records]

    print(f"\nFile: {file_path.name}")
    print("Records:", len(records))
    print("Unique product codes:", len(set(product_codes)))
    print("Duplicate product codes:", len(product_codes) - len(set(product_codes)))
    print("Reported status:", dict(Counter(r.get("isReported") for r in records)))
    print("Aggregate status:", dict(Counter(r.get("isAggregate") for r in records)))

    invalid = [
        r for r in records
        if r.get("primaryValue") is None
    ]
    print("Missing trade values:", len(invalid))

print("\nValidation finished.")
