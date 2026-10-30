
import json
from pathlib import Path
from collections import Counter

file_path = Path("turkey_to_china_2023.json")

with file_path.open("r", encoding="utf-8") as file:
    records = json.load(file)["data"]

print("Toplam kayıt:", len(records))

# Count records by reporting and aggregation status.
status_counts = Counter(
    (r.get("isReported"), r.get("isAggregate"))
    for r in records
)

print("\nRaporlama ve toplulaştırma durumları:")
for status, count in status_counts.items():
    print(status, "->", count)

# Inspect records that are reported and not aggregated.
selected = [
    r for r in records
    if r.get("isReported") is True
    and r.get("isAggregate") is False
]

print("\nReported=True ve Aggregate=False:", len(selected))

for record in selected[:5]:
    print({
        "product": record.get("cmdCode"),
        "value": record.get("primaryValue"),
        "customs": record.get("customsCode"),
        "transport": record.get("motCode"),
        "partner2": record.get("partner2Code"),
        "classification": record.get("classificationCode"),
    })

from collections import Counter

print("\nPartner2 dağılımı:")
print(Counter(str(r.get("partner2Code")) for r in records))

print("\nPartner2 ve raporlama durumu:")
print(Counter(
    (
        str(r.get("partner2Code")),
        r.get("isReported"),
        r.get("isAggregate"),
    )
    for r in records
))
