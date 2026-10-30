"""
config.py — Shared constants and the HS product reference catalogue.

This module is the single source of truth for:
  * UN Comtrade country (reporter/partner) codes for Türkiye and China.
  * Trade-flow codes (1 = Import / 2 = Export) and their valuation rule.
  * The curated HS product catalogue (textiles, lamps, electronics, etc.).
  * Direction definitions used by the UI and the API client.

Keeping these here means the API client, database, analysis, charts and UI
all agree on the same field names and meaning (the team's "shared data
contract").
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict, List, Optional

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
HS_CATALOGUE_PATH = BASE_DIR / "hs_catalogue.json"


def _writable_dir(preferred: Path) -> Path:
    """Return a directory we can actually write to.

    Some hosting sandboxes mount the source tree read-only. SQLite still needs
    a writable location, so fall back to a temp directory rather than crashing
    at import time.
    """
    try:
        preferred.mkdir(parents=True, exist_ok=True)
        probe = preferred / ".write_probe"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()
        return preferred
    except OSError:
        import tempfile

        fallback = Path(tempfile.gettempdir()) / "trade_explorer_data"
        fallback.mkdir(parents=True, exist_ok=True)
        return fallback


DATA_DIR = _writable_dir(BASE_DIR / "data")
DB_PATH = DATA_DIR / "trade.db"


def _load_dotenv() -> None:
    """Minimal .env loader (no dependency). Existing env vars win."""
    env_path = BASE_DIR / ".env"
    if not env_path.exists():
        return
    try:
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, val = line.split("=", 1)
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            if key:
                os.environ.setdefault(key, val)
    except OSError:
        pass


_load_dotenv()

# ---------------------------------------------------------------------------
# UN Comtrade country codes (reporter / partner)
# Source: UN Comtrade country/area codes.
# ---------------------------------------------------------------------------
COUNTRY_CODES = {
    "792": {"iso": "TUR", "name": "Türkiye"},
    "156": {"iso": "CHN", "name": "China"},
}

TURKEY_CODE = "792"
CHINA_CODE = "156"

# ---------------------------------------------------------------------------
# Trade-flow codes and valuation rule.
# UN Comtrade API v1 uses M = Imports (valued CIF), X = Exports (valued FOB).
# ---------------------------------------------------------------------------
FLOW_CODES = {
    "M": {"desc": "Import", "valuation": "CIF"},
    "X": {"desc": "Export", "valuation": "FOB"},
}
IMPORT_FLOW = "M"
EXPORT_FLOW = "X"

# ---------------------------------------------------------------------------
# Directions supported by the MVP.
# We always describe the *reporting* country's export to the *partner*.
# Mirror records (the partner's own import report) may differ and are NOT
# forced to match.
# ---------------------------------------------------------------------------
DIRECTIONS = {
    "TR_TO_CN": {
        "label": "Türkiye → China",
        "description": "Türkiye's exports to China (reporter = Türkiye, partner = China, flow = Export)",
        "reporter_code": TURKEY_CODE,
        "partner_code": CHINA_CODE,
        "flow_code": EXPORT_FLOW,
    },
    "CN_TO_TR": {
        "label": "China → Türkiye",
        "description": "China's exports to Türkiye (reporter = China, partner = Türkiye, flow = Export)",
        "reporter_code": CHINA_CODE,
        "partner_code": TURKEY_CODE,
        "flow_code": EXPORT_FLOW,
    },
}

# ---------------------------------------------------------------------------
# Year range offered in the UI. The latest *available* year depends on the
# specific query; 2025 may be incomplete for some products/flows. Missing
# years are shown explicitly and are NEVER treated as zero.
# ---------------------------------------------------------------------------
DEFAULT_YEAR_MIN = 2010
DEFAULT_YEAR_MAX = 2025  # latest year offered; missing years show as gaps, never zero.

# ---------------------------------------------------------------------------
# Classification / valuation metadata (per the team plan).
# ---------------------------------------------------------------------------
DEFAULT_CLASSIFICATION = "HS"  # Harmonized System
CURRENCY = "USD"

# ---------------------------------------------------------------------------
# HS product reference catalogue.
# A small, curated list covering the product scope in the plan:
# textiles, lamps, electronics, machinery, plastics, steel, etc.
# Users search by name or HS code; ambiguous names surface options.
# ---------------------------------------------------------------------------
HS_CATALOGUE: List[Dict] = [
    {"code": "61", "name": "Articles of apparel, knitted or crocheted", "category": "Textiles"},
    {"code": "62", "name": "Articles of apparel, not knitted or crocheted", "category": "Textiles"},
    {"code": "54", "name": "Man-made filaments; strip and the like", "category": "Textiles"},
    {"code": "55", "name": "Man-made staple fibres", "category": "Textiles"},
    {"code": "57", "name": "Carpets and other textile floor coverings", "category": "Textiles"},
    {"code": "94", "name": "Furniture; bedding, mattresses; lamps and lighting fittings", "category": "Lamps & Furniture"},
    {"code": "9405", "name": "Lamps and lighting fittings, not elsewhere specified", "category": "Lamps & Furniture"},
    {"code": "85", "name": "Electrical machinery and equipment; electronics", "category": "Electronics"},
    {"code": "8517", "name": "Electrical apparatus for line telephony/telegraphy (incl. phones)", "category": "Electronics"},
    {"code": "8528", "name": "Monitors, projectors and television receivers", "category": "Electronics"},
    {"code": "8471", "name": "Automatic data-processing machines (computers)", "category": "Electronics"},
    {"code": "84", "name": "Nuclear reactors, boilers, machinery and mechanical appliances", "category": "Machinery"},
    {"code": "73", "name": "Articles of iron or steel", "category": "Metals"},
    {"code": "39", "name": "Plastics and articles thereof", "category": "Plastics"},
    {"code": "64", "name": "Footwear, gaiters and the like", "category": "Other"},
    {"code": "95", "name": "Toys, games and sports requisites", "category": "Other"},
    {"code": "87", "name": "Vehicles other than railway or tramway rolling stock", "category": "Other"},
]


def load_hs_catalogue() -> List[Dict]:
    """Return the HS catalogue, preferring the JSON file if present.

    The JSON file lets Mert/Tao extend the catalogue without editing code.
    """
    if HS_CATALOGUE_PATH.exists():
        try:
            with open(HS_CATALOGUE_PATH, "r", encoding="utf-8") as fh:
                return json.load(fh)
        except (json.JSONDecodeError, OSError):
            pass
    return HS_CATALOGUE


def search_hs(query: str) -> List[Dict]:
    """Search the catalogue by HS code (exact/substring) or product name.

    Returns a list of matching entries. An empty query returns everything.
    Ambiguous matches (multiple hits) are returned together so the UI can
    show options instead of silently picking one.
    """
    q = (query or "").strip().lower()
    catalogue = load_hs_catalogue()
    if not q:
        return catalogue
    # Exact code match first.
    exact = [c for c in catalogue if c["code"].lower() == q]
    if exact:
        return exact
    # Otherwise substring match on code or name.
    matches = [
        c for c in catalogue
        if q in c["code"].lower() or q in c["name"].lower() or q in c["category"].lower()
    ]
    return matches


def get_hs_entry(code: str) -> Optional[Dict]:
    """Return a single catalogue entry by exact HS code, or None."""
    code = (code or "").strip()
    for c in load_hs_catalogue():
        if c["code"] == code:
            return c
    return None


def country_name(code: str) -> str:
    return COUNTRY_CODES.get(code, {}).get("name", code)


def country_iso(code: str) -> str:
    return COUNTRY_CODES.get(code, {}).get("iso", code)


def flow_desc(code: str) -> str:
    return FLOW_CODES.get(code, {}).get("desc", code)


def valuation_for_flow(code: str) -> str:
    return FLOW_CODES.get(code, {}).get("valuation", "Unknown")


def direction_meta(key: str) -> Dict:
    return DIRECTIONS[key]


# ---------------------------------------------------------------------------
# Runtime configuration (env-overridable)
# ---------------------------------------------------------------------------
def comtrade_base_url() -> str:
    """UN Comtrade API host. Override via env if needed."""
    return os.getenv("COMTRADE_BASE_URL", "https://comtradeapi.un.org")


def comtrade_api_key() -> Optional[str]:
    return os.getenv("COMTRADE_API_KEY") or None


def data_mode() -> str:
    """Which data source to use.

    * "sample"  — bundled deterministic dataset (offline, instant).
    * "live"    — data/v1/get endpoint (needs COMTRADE_API_KEY; higher limits).
    * "preview" — free preview endpoint (no key; 1 period/request, ~2s throttle).

    Default is "preview": real UN Comtrade data with no key required.
    """
    if os.getenv("USE_SAMPLE_DATA", "0") == "1":
        return "sample"
    if os.getenv("USE_LIVE_API", "0") == "1" and comtrade_api_key():
        return "live"
    return "preview"


def use_live_api() -> bool:
    """Kept for backwards compatibility: True when the full (keyed) API is used."""
    return data_mode() == "live"
