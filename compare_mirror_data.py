
import json
from pathlib import Path

folder = Path(__file__).parent

files = {
    "China exports to Turkiye": "china_to_turkey_classic_2023.json",
    "Turkiye exports to China": "turkey_to_china_classic_2023.json",
}

codes_to_check = {
    "China exports to Turkiye": ["5102", "382213", "854340"],
    "Turkiye exports to China": ["401610", "852412", "2505"],
}

fields = [
    "cmdCode",
    "primaryValue",
    "isReported",
    "isAggregate",
    "classificationCode",
    "legacyEstimationFlag",
    "fobvalue",
    "cifvalue",
]

for name, filename in files.items():
    path = folder / filename

    if not path.exists():
        print(f"\nDosya bulunamadi: {filename}")
        continue

    with path.open("r", encoding="utf-8") as file:
        content = json.load(file)

    records = content.get("data", content) if isinstance(content, dict) else content

    print(f"\n=== {name} ===")

    for code in codes_to_check[name]:
        matches = [
            row for row in records
            if str(row.get("cmdCode")) == code
        ]

        if not matches:
            print(f"HS {code}: dosyada bulunamadi")
            continue

        for row in matches[:3]:
            print(f"\nHS {code}")
            for field in fields:
                print(f"  {field}: {row.get(field)}")
