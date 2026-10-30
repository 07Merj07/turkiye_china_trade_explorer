"""
sample_data.py — Deterministic, offline sample dataset.

Why this exists
---------------
The live UN Comtrade API needs a subscription key and network access. So the
whole application can still be built, tested and demoed, this module produces
realistic annual trade totals for Türkiye↔China using a fixed seed. The output
mirrors the real API record shape (v1 field names) so the same normaliser,
database, analysis and charts run unchanged.

Each query returns:
  * one aggregate/total row   (isAggregate=True)  -> is_total = 1
  * three breakdown rows      (isAggregate=False) -> is_total = 0
The breakdown rows sum to the total on purpose: this reproduces the real
"multiple customs / transport breakdowns" trap, and proves the ingestion and
analysis only ever use the total row (no double counting).
"""

from __future__ import annotations

import hashlib
import math
import random
from typing import Any, Dict, List

import config

# Approximate latest-year baseline export values (USD) per direction.
# TR_TO_CN = Türkiye's exports to China; CN_TO_TR = China's exports to Türkiye.
BASE_VALUES: Dict[str, Dict[str, float]] = {
    "61":   {"TR_TO_CN": 15_000_000,  "CN_TO_TR": 900_000_000},
    "62":   {"TR_TO_CN": 10_000_000,  "CN_TO_TR": 700_000_000},
    "54":   {"TR_TO_CN": 5_000_000,   "CN_TO_TR": 300_000_000},
    "55":   {"TR_TO_CN": 8_000_000,   "CN_TO_TR": 250_000_000},
    "57":   {"TR_TO_CN": 12_000_000,  "CN_TO_TR": 120_000_000},
    "94":   {"TR_TO_CN": 20_000_000,  "CN_TO_TR": 1_200_000_000},
    "9405": {"TR_TO_CN": 6_000_000,   "CN_TO_TR": 800_000_000},
    "85":   {"TR_TO_CN": 40_000_000,  "CN_TO_TR": 8_000_000_000},
    "8517": {"TR_TO_CN": 10_000_000,  "CN_TO_TR": 3_000_000_000},
    "8528": {"TR_TO_CN": 5_000_000,   "CN_TO_TR": 2_000_000_000},
    "8471": {"TR_TO_CN": 8_000_000,   "CN_TO_TR": 2_500_000_000},
    "84":   {"TR_TO_CN": 60_000_000,  "CN_TO_TR": 6_000_000_000},
    "73":   {"TR_TO_CN": 30_000_000,  "CN_TO_TR": 1_500_000_000},
    "39":   {"TR_TO_CN": 45_000_000,  "CN_TO_TR": 2_000_000_000},
    "64":   {"TR_TO_CN": 3_000_000,   "CN_TO_TR": 400_000_000},
    "95":   {"TR_TO_CN": 2_000_000,   "CN_TO_TR": 600_000_000},
    "87":   {"TR_TO_CN": 25_000_000,  "CN_TO_TR": 1_800_000_000},
}

YEAR_START = 2010
YEAR_END = config.DEFAULT_YEAR_MAX


def _direction_key(reporter: str, partner: str) -> str:
    if reporter == config.TURKEY_CODE and partner == config.CHINA_CODE:
        return "TR_TO_CN"
    if reporter == config.CHINA_CODE and partner == config.TURKEY_CODE:
        return "CN_TO_TR"
    # Fallback: treat as TR->CN shape.
    return "TR_TO_CN"


def _seed(*parts: Any) -> int:
    h = hashlib.sha256("|".join(map(str, parts)).encode("utf-8")).hexdigest()
    return int(h[:8], 16)


def _base_value(commodity: str, direction: str) -> float:
    entry = BASE_VALUES.get(commodity)
    if entry:
        return entry[direction]
    # Unknown commodity: derive a plausible value from its HS chapter.
    chapter = commodity[:2]
    parent = BASE_VALUES.get(chapter)
    if parent:
        return parent[direction] * 0.15
    return 20_000_000 if direction == "TR_TO_CN" else 500_000_000


def _growth(year: int) -> float:
    """Smooth rise from ~0.35 (2010) to ~1.0 (the latest configured year)."""
    span = max(1, YEAR_END - YEAR_START)
    t = (year - YEAR_START) / span
    return 0.35 + 0.65 * t


def _year_factor(commodity: str, direction: str, year: int) -> float:
    rnd = random.Random(_seed(commodity, direction, year))
    return 1.0 + rnd.uniform(-0.07, 0.07)


def _value_for_year(commodity: str, direction: str, year: int) -> float:
    base = _base_value(commodity, direction)
    value = base * _growth(year) * _year_factor(commodity, direction, year)
    return round(value, 0)


def _commodity_desc(commodity: str) -> str:
    entry = config.get_hs_entry(commodity)
    return entry["name"] if entry else f"HS {commodity}"


def _record(
    reporter: str,
    partner: str,
    flow: str,
    commodity: str,
    year: int,
    value: float,
    *,
    is_aggregate: bool,
    customs_code: str = "0",
    mot_code: str = "0",
    partner2_code: str = "0",
) -> Dict[str, Any]:
    return {
        "reporterCode": reporter,
        "reporterISO": config.country_iso(reporter),
        "reporterDesc": config.country_name(reporter),
        "partnerCode": partner,
        "partnerISO": config.country_iso(partner),
        "partnerDesc": config.country_name(partner),
        "flowCode": flow,
        "flowDesc": config.flow_desc(flow),
        "cmdCode": commodity,
        "cmdDesc": _commodity_desc(commodity),
        "period": str(year),
        "refYear": year,
        "primaryValue": value,
        "netWgt": round(value / 8.0, 1) if value else 0.0,
        "qty": None,
        "qtyUnitAbbr": None,
        "cifvalue": value if flow == config.IMPORT_FLOW else None,
        "fobvalue": value if flow == config.EXPORT_FLOW else None,
        "customsCode": customs_code,
        "motCode": mot_code,
        "partner2Code": partner2_code,
        "isAggregate": is_aggregate,
        "classificationCode": "HS",
        "flag": "0",
        "flagDesc": "",
    }


def generate_records(
    reporter: str, partner: str, year: int, flow: str, commodity: str
) -> List[Dict[str, Any]]:
    """Return total + breakdown rows for one (reporter, partner, year, flow, commodity)."""
    if year < 1962 or year > 2100:
        return []

    direction = _direction_key(reporter, partner)
    total = _value_for_year(commodity, direction, year)
    if total <= 0:
        return []

    records: List[Dict[str, Any]] = [
        _record(reporter, partner, flow, commodity, year, total, is_aggregate=True)
    ]

    # Breakdown rows that sum to the total (customs regimes 55% / 30% / 15%).
    # Codes avoid "C00" because that is the real API's *aggregate* customs code.
    for customs_code, share in (("C01", 0.55), ("C02", 0.30), ("C03", 0.15)):
        records.append(
            _record(
                reporter, partner, flow, commodity, year, round(total * share, 0),
                is_aggregate=False, customs_code=customs_code, mot_code="0",
            )
        )
    return records


def available_years(commodity: str, reporter: str, partner: str) -> List[int]:
    """Years the sample provider can serve (the full configured range)."""
    direction = _direction_key(reporter, partner)
    years = []
    for y in range(YEAR_START, YEAR_END + 1):
        if _value_for_year(commodity, direction, y) > 0:
            years.append(y)
    return years
