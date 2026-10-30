import json
from pathlib import Path

# Read the API response.
file_path = Path("response_1792842463800.json")

with file_path.open("r", encoding="utf-8") as file:
    response = json.load(file)

records = response.get("data", [])

# Select the candidate annual total.
selected = [
    record for record in records
    if record["refYear"] == 2023
    and record["cmdCode"] == "610910"
    and record["partner2ISO"] == "W00"
    and record["customsCode"] == "C00"
    and record["motCode"] == 0
]

print("Matching records:", len(selected))

if len(selected) != 1:
    raise ValueError("Expected exactly one candidate record.")

record = selected[0]

# Display the fields needed for validation.
fields = [
    "reporterISO", "partnerISO", "flowCode", "flowDesc",
    "refYear", "cmdCode", "classificationCode",
    "primaryValue", "cifvalue", "fobvalue",
    "isReported", "isAggregate"
]

for field in fields:
    print(f"{field}: {record.get(field)}")