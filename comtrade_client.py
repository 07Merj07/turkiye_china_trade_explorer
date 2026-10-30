"""
comtrade_client.py — UN Comtrade API integration (v1, real endpoints).

Verified endpoints (Oct 2026):

    GET {BASE}/public/v1/preview/C/A/HS      # free, no key, 1 period/request
    GET {BASE}/data/v1/get/C/A/HS            # full data, needs subscription key

    query params: reporterCode, partnerCode, period, flowCode (M=import, X=export),
                  cmdCode, includeDesc=true

Modes (see config.data_mode):
  * "preview" — real data, no key, rate-limited (~1 request / 2 s)
  * "live"    — real data via data/v1/get, requires COMTRADE_API_KEY
  * "sample"  — bundled deterministic dataset (offline, instant)

On any live failure the client falls back to the sample dataset so the app
stays usable, and reports the failure in `FetchResult.message`.
"""

from __future__ import annotations

import datetime as _dt
import json
import re
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import config
import sample_data

try:
    import requests  # type: ignore
except Exception:  # pragma: no cover
    requests = None


# ---------------------------------------------------------------------------
# Result object
# ---------------------------------------------------------------------------
@dataclass
class FetchResult:
    records: List[Dict[str, Any]]
    query_params: Dict[str, Any]
    source: str
    retrieved_at: str
    status: str  # "ok" | "empty" | "error" | "fallback"
    message: str = ""
    mode: str = "preview"  # "preview" | "live" | "sample"
    http_status: Optional[int] = None
    live_error: str = ""
    raw_count: int = 0


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _first(rec: Dict[str, Any], keys: List[str]) -> Any:
    for k in keys:
        if k in rec and rec[k] is not None:
            return rec[k]
    return None


def _to_float(value: Any) -> Optional[float]:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _to_int(value: Any) -> Optional[int]:
    f = _to_float(value)
    return int(f) if f is not None else None


def _now_iso() -> str:
    return _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0).isoformat()


def _str(value: Any) -> str:
    """Stringify without turning 0 into an empty string."""
    return "" if value is None else str(value)


def _is_aggregate_row(rec: Dict[str, Any]) -> bool:
    """True only for the *total* row across all secondary dimensions.

    Note: the API's `isAggregate` flag is True for every row of an aggregated
    dataset, so it must NOT be used here. The true total has customsCode "C00"
    (all customs procedures), motCode 0 (all transport modes) and
    partner2Code 0 (second partner = World).
    """
    def _agg(value: Any) -> bool:
        if value is None:
            return True
        s = str(value).strip().lower()
        return s in {"", "0", "all", "world", "total", "w00", "c00"}

    customs = _first(rec, ["customsCode", "customs"])
    mot = _first(rec, ["motCode", "modeOfTransportCode", "mosCode"])
    partner2 = _first(rec, ["partner2Code", "pt2Code"])
    return _agg(customs) and _agg(mot) and _agg(partner2)


def _normalize_record(rec: Dict[str, Any], meta: Dict[str, Any]) -> Dict[str, Any]:
    """Map a raw Comtrade record to the shared internal contract."""
    reporter_code = str(_first(rec, ["reporterCode", "rtCode"]) or meta["reporter"])
    partner_code = str(_first(rec, ["partnerCode", "ptCode"]) or meta["partner"])
    flow_code = str(_first(rec, ["flowCode", "rgCode"]) or meta["flow"])
    commodity_code = str(_first(rec, ["cmdCode", "commodityCode"]) or meta["commodity"])

    period = _first(rec, ["period", "refYear", "yr"]) or meta["year"]
    year = _to_int(period) or _to_int(meta["year"])

    return {
        "reporter_code": reporter_code,
        "reporter_iso": _first(rec, ["reporterISO", "rtISO"]) or config.country_iso(reporter_code),
        "reporter_name": _first(rec, ["reporterDesc", "rtTitle"]) or config.country_name(reporter_code),
        "partner_code": partner_code,
        "partner_iso": _first(rec, ["partnerISO", "ptISO"]) or config.country_iso(partner_code),
        "partner_name": _first(rec, ["partnerDesc", "ptTitle"]) or config.country_name(partner_code),
        "flow_code": flow_code,
        "flow_desc": _first(rec, ["flowDesc", "rgDesc"]) or config.flow_desc(flow_code),
        "commodity_code": commodity_code,
        "commodity_desc": _first(rec, ["cmdDesc", "commodityDesc"]) or meta.get("commodity_desc", ""),
        "classification": _first(rec, ["classificationCode", "classificationSearchCode", "px"]) or meta["classification"],
        "year": year,
        "period": str(period),
        "trade_value": _to_float(_first(rec, ["primaryValue", "tradeValue"])),
        "net_weight": _to_float(_first(rec, ["netWgt", "netWeight"])),
        "quantity": _to_float(_first(rec, ["qty", "quantity"])),
        "qty_unit": _first(rec, ["qtyUnitAbbr", "qtyUnit"]) or "",
        "cif_value": _to_float(_first(rec, ["cifvalue", "cifValue"])),
        "fob_value": _to_float(_first(rec, ["fobvalue", "fobValue"])),
        "valuation": config.valuation_for_flow(flow_code),
        "flag": _str(_first(rec, ["flag", "legacyEstimationFlag"])),
        "flag_desc": _first(rec, ["flagDesc"]) or "",
        "customs_code": _str(_first(rec, ["customsCode", "customs"])),
        "mot_code": _str(_first(rec, ["motCode", "mosCode"])),
        "partner2_code": _str(_first(rec, ["partner2Code", "pt2Code"])),
        "is_total": 1 if _is_aggregate_row(rec) else 0,
        "source": "UN Comtrade",
        "retrieved_at": meta["retrieved_at"],
        "query_params": json.dumps(meta["query_params"], sort_keys=True),
    }


# ---------------------------------------------------------------------------
# Throttle (shared across client instances, for the rate-limited preview API)
# ---------------------------------------------------------------------------
_THROTTLE_LOCK = threading.Lock()
_LAST_CALL = 0.0


def _throttle(min_interval: float) -> None:
    global _LAST_CALL
    with _THROTTLE_LOCK:
        wait = min_interval - (time.time() - _LAST_CALL)
        if wait > 0:
            time.sleep(wait)
        _LAST_CALL = time.time()


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------
class ComtradeClient:
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        mode: Optional[str] = None,
        timeout: int = 30,
        max_retries: int = 4,
        throttle: float = 2.2,
    ):
        self.api_key = api_key if api_key is not None else config.comtrade_api_key()
        self.base_url = (base_url or config.comtrade_base_url()).rstrip("/")
        self.mode = mode or config.data_mode()
        self.timeout = timeout
        self.max_retries = max_retries
        # Keep a small gap even on the keyed endpoint: it enforces a low
        # per-second rate limit, and parallel bursts trigger 429s.
        self.throttle = 0.5 if self.mode == "live" else throttle

    # -- URL / params -------------------------------------------------------
    def build_url(self) -> str:
        # C = goods, A = annual, HS = HS classification.
        if self.mode == "live":
            # Full data (aggregate + breakdowns), requires a subscription key.
            return f"{self.base_url}/data/v1/get/C/A/HS"
        # Free preview (aggregate only), no key.
        return f"{self.base_url}/public/v1/preview/C/A/HS"

    def build_params(self, reporter: str, partner: str, year: int, flow: str, commodity: str) -> Dict[str, Any]:
        params = {
            "reporterCode": reporter,
            "partnerCode": partner,
            "period": str(year),
            "flowCode": flow,          # M = import, X = export
            "cmdCode": commodity,
            "includeDesc": "true",
        }
        if self.mode == "live":
            params["format"] = "JSON"
            params["maxRecords"] = "500"
        return params

    # -- Public entry point -------------------------------------------------
    def fetch(
        self,
        reporter: str,
        partner: str,
        year: int,
        flow: str,
        commodity: str,
        classification: str = config.DEFAULT_CLASSIFICATION,
        commodity_desc: str = "",
    ) -> FetchResult:
        params = self.build_params(reporter, partner, year, flow, commodity)
        meta = {
            "reporter": reporter, "partner": partner, "year": year, "flow": flow,
            "commodity": commodity, "classification": classification,
            "commodity_desc": commodity_desc, "query_params": params,
            "retrieved_at": _now_iso(),
        }

        if self.mode == "sample":
            raw = sample_data.generate_records(reporter, partner, int(year), flow, commodity)
            records = [_normalize_record(r, meta) for r in raw]
            return FetchResult(
                records=records, query_params=params,
                source="UN Comtrade (sample dataset)", retrieved_at=meta["retrieved_at"],
                status="ok" if records else "empty",
                message="" if records else "No data in sample dataset for this query.",
                mode="sample", raw_count=len(records),
            )

        return self._fetch_live(params, meta)

    # -- Live request -------------------------------------------------------
    def _fetch_live(self, params: Dict[str, Any], meta: Dict[str, Any]) -> FetchResult:
        url = self.build_url()
        headers = {"Accept": "application/json", "User-Agent": "TurkiyeChinaTradeExplorer/1.1"}
        if self.mode == "live" and self.api_key:
            headers["Ocp-Apim-Subscription-Key"] = self.api_key

        if requests is None:
            return self._fallback(params, meta, "requests library unavailable", None)

        last_error = ""
        http_status: Optional[int] = None

        for attempt in range(1, self.max_retries + 1):
            _throttle(self.throttle)
            try:
                resp = requests.get(url, params=params, headers=headers, timeout=self.timeout)
                http_status = resp.status_code
            except Exception as exc:
                last_error = f"Network error: {exc}"
                if attempt < self.max_retries:
                    time.sleep(min(2 ** attempt, 8))
                    continue
                return self._fallback(params, meta, last_error, http_status)

            if resp.status_code == 200:
                try:
                    payload = resp.json()
                except ValueError:
                    return self._fallback(params, meta, "Invalid JSON in response", 200)
                return self._parse_live_payload(payload, params, meta)

            if resp.status_code == 400:
                return self._fallback(params, meta, f"Bad request: {self._err(resp)}", 400)

            if resp.status_code in (401, 403):
                return self._fallback(
                    params, meta,
                    "Authentication failed (401/403): check COMTRADE_API_KEY for data/v1/get.", resp.status_code,
                )

            if resp.status_code == 404:
                return self._fallback(
                    params, meta, "Endpoint not found (404): check COMTRADE_BASE_URL.", resp.status_code,
                )

            if resp.status_code == 429:
                wait = self._retry_after(resp)
                last_error = f"Rate limited (429). Waited {wait}s (attempt {attempt}/{self.max_retries})."
                if attempt < self.max_retries:
                    time.sleep(wait)
                    continue
                return self._fallback(params, meta, last_error, resp.status_code)

            if 500 <= resp.status_code < 600:
                last_error = f"Server error ({resp.status_code})."
                if attempt < self.max_retries:
                    time.sleep(min(2 ** attempt, 8))
                    continue
                return self._fallback(params, meta, last_error, resp.status_code)

            return self._fallback(params, meta, f"Unexpected HTTP {resp.status_code}.", resp.status_code)

        return self._fallback(params, meta, last_error or "Unknown error", http_status)

    # -- Response parsing ---------------------------------------------------
    def _parse_live_payload(self, payload: Any, params: Dict[str, Any], meta: Dict[str, Any]) -> FetchResult:
        source = "UN Comtrade (preview API)" if self.mode == "preview" else "UN Comtrade"

        if isinstance(payload, dict):
            if payload.get("error"):
                return self._fallback(params, meta, f"API error: {payload['error']}", 200)
            raw = payload.get("data") or payload.get("dataset") or []
        elif isinstance(payload, list):
            raw = payload
        else:
            raw = []

        if not raw:
            return FetchResult(
                records=[], query_params=params, source=source,
                retrieved_at=meta["retrieved_at"], status="empty",
                message="No records returned for this query. Missing data is not treated as zero.",
                mode=self.mode, http_status=200, raw_count=0,
            )

        records = [_normalize_record(r, meta) for r in raw]
        usable = [r for r in records if r.get("trade_value") is not None]
        return FetchResult(
            records=usable, query_params=params, source=source,
            retrieved_at=meta["retrieved_at"],
            status="ok" if usable else "empty",
            message="" if usable else "Records returned but none contained a usable value.",
            mode=self.mode, http_status=200, raw_count=len(records),
        )

    # -- Fallback -----------------------------------------------------------
    def _fallback(self, params, meta, error: str, http_status) -> FetchResult:
        raw = sample_data.generate_records(
            params["reporterCode"], params["partnerCode"], int(params["period"]),
            params["flowCode"], params["cmdCode"],
        )
        records = [_normalize_record(r, meta) for r in raw]
        return FetchResult(
            records=records, query_params=params,
            source="UN Comtrade (sample dataset — live API unavailable)",
            retrieved_at=meta["retrieved_at"], status="fallback",
            message=f"Live API failed: {error} Showing sample data so the app remains usable.",
            mode="sample", http_status=http_status, live_error=error, raw_count=len(records),
        )

    # -- Error helpers ------------------------------------------------------
    @staticmethod
    def _err(resp) -> str:
        try:
            body = resp.json()
            if isinstance(body, dict):
                return str(body.get("error") or body.get("message") or body)[:160]
        except Exception:
            pass
        return (resp.text or "")[:160]

    @staticmethod
    def _retry_after(resp) -> int:
        ra = resp.headers.get("Retry-After")
        if ra and str(ra).isdigit():
            return int(ra)
        try:
            msg = str(resp.json().get("message", ""))
            m = re.search(r"in\s+(\d+)\s+second", msg)
            if m:
                return int(m.group(1)) + 1
        except Exception:
            pass
        return 3


# ---------------------------------------------------------------------------
# Convenience + audit
# ---------------------------------------------------------------------------
def fetch_trade_data(
    reporter: str,
    partner: str,
    year: int,
    flow: str,
    commodity: str,
    classification: str = config.DEFAULT_CLASSIFICATION,
    commodity_desc: str = "",
    client: Optional[ComtradeClient] = None,
) -> FetchResult:
    client = client or ComtradeClient()
    return client.fetch(
        reporter=reporter, partner=partner, year=year, flow=flow,
        commodity=commodity, classification=classification, commodity_desc=commodity_desc,
    )


def save_response(result: FetchResult, directory: Optional[Path] = None) -> Path:
    """Persist the exact query parameters + normalized response (audit trail)."""
    directory = directory or (config.DATA_DIR / "responses")
    directory.mkdir(parents=True, exist_ok=True)
    stamp = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    q = result.query_params
    name = f"ct_{q.get('reporterCode')}_{q.get('partnerCode')}_{q.get('period')}_{q.get('flowCode')}_{q.get('cmdCode')}_{stamp}.json"
    path = directory / name
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(
            {
                "query_params": result.query_params, "source": result.source,
                "retrieved_at": result.retrieved_at, "mode": result.mode,
                "status": result.status, "message": result.message, "records": result.records,
            },
            fh, ensure_ascii=False, indent=2,
        )
    return path
