
import json
from pathlib import Path
from collections import Counter

files = sorted(Path(".").glob("*_classic_20*.json"))

for path in files:
    with path.open("r", encoding="utf-8") as file:
        records = json.load(file).get("data", [])

    print(f"\n--- {path.name} ---")
    print("Records:", len(records))

    print("Product levels:", dict(Counter(
        str(r.get("aggrLevel")) for r in records
    )))

    print("Leaf status:", dict(Counter(
        str(r.get("isLeaf")) for r in records
    )))

    print("Reported status:", dict(Counter(
        str(r.get("isReported")) for r in records
    )))

    print("Missing values:", sum(
        r.get("primaryValue") is None for r in records
    ))

    keys = [
        (r.get("refYear"), r.get("cmdCode"), r.get("classificationCode"))
        for r in records
    ]
    print("Repeated product keys:", len(keys) - len(set(keys)))

print("\nValidation finished.")
