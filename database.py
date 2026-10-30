"""
database.py — SQLite schema, ingestion, SQL queries and validation.

Implements the data-side contract that Tao owns on the application side and
that Mert validates:

  * A schema that preserves source / query / classification / flow / partner /
    valuation metadata for every observation.
  * A uniqueness rule based on the real dimensions, enforced with a UNIQUE
    constraint so re-running an ingestion never inserts duplicates.
  * A hard separation between the aggregate total row (is_total = 1) and
    detailed breakdowns (is_total = 0). Analysis only ever reads totals, so
    customs / transport / second-partner breakdowns can never double-count.
  * SQL for annual totals and year-over-year change (window function).
  * A validation routine for duplicates, missing values and suspicious rows.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

import config

# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------
SCHEMA = """
CREATE TABLE IF NOT EXISTS trade_records (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    reporter_code   TEXT NOT NULL,
    reporter_iso    TEXT,
    reporter_name   TEXT,
    partner_code    TEXT NOT NULL,
    partner_iso     TEXT,
    partner_name    TEXT,
    flow_code       TEXT NOT NULL,
    flow_desc       TEXT,
    commodity_code  TEXT NOT NULL,
    commodity_desc  TEXT,
    classification  TEXT NOT NULL,
    year            INTEGER NOT NULL,
    period          TEXT,
    trade_value     REAL,
    net_weight      REAL,
    quantity        REAL,
    qty_unit        TEXT,
    cif_value       REAL,
    fob_value       REAL,
    valuation       TEXT,
    flag            TEXT,
    flag_desc       TEXT,
    is_total        INTEGER NOT NULL DEFAULT 1,
    is_sample       INTEGER NOT NULL DEFAULT 0,
    source          TEXT,
    retrieved_at    TEXT,
    query_params    TEXT,
    UNIQUE(reporter_code, partner_code, flow_code, commodity_code,
           year, classification, period, is_total, is_sample)
);

CREATE INDEX IF NOT EXISTS idx_trade_lookup
    ON trade_records(reporter_code, partner_code, flow_code, commodity_code, year);

CREATE TABLE IF NOT EXISTS raw_records (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    record_hash    TEXT UNIQUE,
    reporter_code  TEXT,
    partner_code   TEXT,
    flow_code      TEXT,
    commodity_code TEXT,
    year           INTEGER,
    period         TEXT,
    customs_code   TEXT,
    mot_code       TEXT,
    partner2_code  TEXT,
    trade_value    REAL,
    is_total       INTEGER,
    is_sample      INTEGER NOT NULL DEFAULT 0,
    query_params   TEXT,
    retrieved_at   TEXT
);

CREATE TABLE IF NOT EXISTS ingest_log (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    query_params  TEXT,
    source        TEXT,
    mode          TEXT,
    status        TEXT,
    message       TEXT,
    raw_count     INTEGER,
    total_rows    INTEGER,
    inserted      INTEGER,
    retrieved_at  TEXT
);

CREATE TABLE IF NOT EXISTS fetch_attempts (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    reporter_code  TEXT NOT NULL,
    partner_code   TEXT NOT NULL,
    flow_code      TEXT NOT NULL,
    commodity_code TEXT NOT NULL,
    period         TEXT NOT NULL,
    mode           TEXT NOT NULL,
    status         TEXT,
    record_count   INTEGER,
    retrieved_at   TEXT,
    UNIQUE(reporter_code, partner_code, flow_code, commodity_code, period, mode)
);
"""


# ---------------------------------------------------------------------------
# Mode isolation
# ---------------------------------------------------------------------------
def sample_flag() -> int:
    """Which rows belong to the ACTIVE mode.

    0 = real UN Comtrade data, 1 = bundled sample/fallback data.

    Every read filters on this flag, so a fallback can never be mixed into a
    real series (that is what used to produce two "totals" for the same year).
    In sample mode the app reads only sample rows, in real mode only real ones.
    """
    return 1 if config.data_mode() == "sample" else 0


# ---------------------------------------------------------------------------
# Connection / init
# ---------------------------------------------------------------------------
def get_connection(db_path: Optional[Path] = None) -> sqlite3.Connection:
    db_path = Path(db_path or config.DB_PATH)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    _migrate(conn)
    conn.commit()


def _migrate(conn: sqlite3.Connection) -> None:
    """Add columns introduced after the first schema (old DBs keep working)."""
    for table in ("trade_records", "raw_records"):
        cols = {row[1] for row in conn.execute(f"PRAGMA table_info({table})")}
        if "is_sample" not in cols:
            conn.execute(
                f"ALTER TABLE {table} ADD COLUMN is_sample INTEGER NOT NULL DEFAULT 0"
            )


# ---------------------------------------------------------------------------
# Ingestion
# ---------------------------------------------------------------------------
def _record_hash(rec: Dict[str, Any], is_sample: int = 0) -> str:
    key = "|".join(
        str(rec.get(k, ""))
        for k in (
            "reporter_code", "partner_code", "flow_code", "commodity_code",
            "year", "period", "customs_code", "mot_code", "partner2_code", "is_total",
        )
    )
    # Sample rows must not collide with real rows in the audit table.
    return hashlib.sha256(f"{key}|sample={is_sample}".encode("utf-8")).hexdigest()


def upsert_records(conn: sqlite3.Connection, result) -> Dict[str, int]:
    """Archive all raw rows, then insert only total rows into trade_records.

    Sample / fallback payloads are stored with is_sample = 1 so they can never
    be mixed into the real analysis series (every read filters is_sample = 0).
    This is what keeps a fallback from silently contaminating real figures.

    Returns counts so callers can report "N new, M skipped (duplicate)".
    """
    is_sample = 1 if getattr(result, "mode", "preview") == "sample" else 0
    totals = [r for r in result.records if int(r.get("is_total", 0)) == 1]
    note = ""
    if not totals and result.records:
        if len(result.records) == 1:
            # A single record can safely be treated as the total.
            result.records[0]["is_total"] = 1
            totals = [result.records[0]]
            note = "No aggregate flag present; single record used as total."
        else:
            # Multiple un-flagged rows: refuse to guess or sum blindly.
            note = (
                f"No aggregate row identified among {len(result.records)} records; "
                f"nothing stored (refusing to sum breakdowns blindly)."
            )

    total_ids = {id(r) for r in totals}
    breakdowns = [r for r in result.records if id(r) not in total_ids]

    # 1) Archive every raw row (including breakdowns) for audit, dedup by hash.
    raw_inserted = 0
    for rec in result.records:
        cur = conn.execute(
            """INSERT OR IGNORE INTO raw_records
               (record_hash, reporter_code, partner_code, flow_code, commodity_code,
                year, period, customs_code, mot_code, partner2_code, trade_value,
                is_total, is_sample, query_params, retrieved_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                _record_hash(rec, is_sample), rec.get("reporter_code"), rec.get("partner_code"),
                rec.get("flow_code"), rec.get("commodity_code"), rec.get("year"),
                rec.get("period"), rec.get("customs_code"), rec.get("mot_code"),
                rec.get("partner2_code"), rec.get("trade_value"), rec.get("is_total"),
                is_sample, rec.get("query_params"), rec.get("retrieved_at"),
            ),
        )
        raw_inserted += cur.rowcount

    # 2) Insert totals into the analysis table. UNIQUE constraint dedups reruns.
    inserted = 0
    for rec in totals:
        cur = conn.execute(
            """INSERT OR IGNORE INTO trade_records
               (reporter_code, reporter_iso, reporter_name, partner_code, partner_iso,
                partner_name, flow_code, flow_desc, commodity_code, commodity_desc,
                classification, year, period, trade_value, net_weight, quantity,
                qty_unit, cif_value, fob_value, valuation, flag, flag_desc,
                is_total, is_sample, source, retrieved_at, query_params)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                rec.get("reporter_code"), rec.get("reporter_iso"), rec.get("reporter_name"),
                rec.get("partner_code"), rec.get("partner_iso"), rec.get("partner_name"),
                rec.get("flow_code"), rec.get("flow_desc"), rec.get("commodity_code"),
                rec.get("commodity_desc"), rec.get("classification"), rec.get("year"),
                rec.get("period"), rec.get("trade_value"), rec.get("net_weight"),
                rec.get("quantity"), rec.get("qty_unit"), rec.get("cif_value"),
                rec.get("fob_value"), rec.get("valuation"), rec.get("flag"),
                rec.get("flag_desc"), 1, is_sample, rec.get("source"),
                rec.get("retrieved_at"), rec.get("query_params"),
            ),
        )
        inserted += cur.rowcount

    # 3) Log the ingestion.
    conn.execute(
        """INSERT INTO ingest_log
           (query_params, source, mode, status, message, raw_count, total_rows, inserted, retrieved_at)
           VALUES (?,?,?,?,?,?,?,?,?)""",
        (
            json.dumps(result.query_params, sort_keys=True), result.source, result.mode,
            result.status, (result.message + (" " + note if note else "")).strip(),
            result.raw_count, len(totals), inserted, result.retrieved_at,
        ),
    )

    # 4) Record the attempt itself, so a bulk build can resume without
    #    re-querying years that legitimately have no data.
    q = result.query_params or {}
    conn.execute(
        """INSERT OR REPLACE INTO fetch_attempts
           (reporter_code, partner_code, flow_code, commodity_code, period,
            mode, status, record_count, retrieved_at)
           VALUES (?,?,?,?,?,?,?,?,?)""",
        (
            str(q.get("reporterCode", "")), str(q.get("partnerCode", "")),
            str(q.get("flowCode", "")), str(q.get("cmdCode", "")),
            str(q.get("period", "")), result.mode, result.status,
            len(result.records), result.retrieved_at,
        ),
    )
    conn.commit()

    return {
        "totals": len(totals),
        "breakdowns": len(breakdowns),
        "raw_inserted": raw_inserted,
        "inserted": inserted,
        "skipped": len(totals) - inserted,
        "note": note,
        "is_sample": is_sample,
    }


# ---------------------------------------------------------------------------
# Queries
# ---------------------------------------------------------------------------
def fetch_series(
    conn: sqlite3.Connection,
    reporter: str,
    partner: str,
    flow: str,
    commodity: str,
    year_min: int,
    year_max: int,
) -> List[Dict[str, Any]]:
    """Return annual total rows for one exact direction/product (totals only).

    Guarantees **at most one row per year**, so a year can never be counted
    twice. Sample/fallback rows are excluded. If more than one real total row
    exists for a year (e.g. two HS revisions were stored), the most recently
    retrieved one wins.
    """
    rows = conn.execute(
        """WITH ranked AS (
               SELECT year, trade_value, net_weight, valuation, classification,
                      reporter_name, partner_name, flow_desc, commodity_desc, retrieved_at,
                      ROW_NUMBER() OVER (
                          PARTITION BY year ORDER BY retrieved_at DESC, id DESC
                      ) AS rn
               FROM trade_records
               WHERE reporter_code = ? AND partner_code = ? AND flow_code = ?
                 AND commodity_code = ? AND is_total = 1 AND is_sample = ?
                 AND year BETWEEN ? AND ?
           )
           SELECT year, trade_value, net_weight, valuation, classification,
                  reporter_name, partner_name, flow_desc, commodity_desc, retrieved_at
           FROM ranked WHERE rn = 1
           ORDER BY year""",
        (reporter, partner, flow, commodity, sample_flag(), year_min, year_max),
    ).fetchall()
    return [dict(r) for r in rows]


def fetch_direction_series(
    conn: sqlite3.Connection, direction_key: str, commodity: str, year_min: int, year_max: int
) -> List[Dict[str, Any]]:
    d = config.direction_meta(direction_key)
    return fetch_series(
        conn, d["reporter_code"], d["partner_code"], d["flow_code"], commodity, year_min, year_max
    )


def cached_years(
    conn: sqlite3.Connection, direction_key: str, commodity: str, year_min: int, year_max: int
) -> set:
    """Years already stored for this direction/product in the active mode."""
    d = config.direction_meta(direction_key)
    rows = conn.execute(
        """SELECT DISTINCT year FROM trade_records
           WHERE reporter_code=? AND partner_code=? AND flow_code=? AND commodity_code=?
             AND is_total=1 AND is_sample=? AND year BETWEEN ? AND ?""",
        (d["reporter_code"], d["partner_code"], d["flow_code"], commodity,
         sample_flag(), year_min, year_max),
    ).fetchall()
    return {r[0] for r in rows}


def attempted_years(
    conn: sqlite3.Connection, direction_key: str, commodity: str, year_min: int, year_max: int
) -> set:
    """Years already queried successfully (ok or legitimately empty).

    Used to resume a bulk build without re-querying years that have no data,
    and to avoid burning rate limit on repeat page loads.
    """
    d = config.direction_meta(direction_key)
    rows = conn.execute(
        """SELECT DISTINCT CAST(period AS INTEGER) FROM fetch_attempts
           WHERE reporter_code=? AND partner_code=? AND flow_code=? AND commodity_code=?
             AND mode=? AND status IN ('ok','empty')
             AND CAST(period AS INTEGER) BETWEEN ? AND ?""",
        (d["reporter_code"], d["partner_code"], d["flow_code"], commodity,
         config.data_mode(), year_min, year_max),
    ).fetchall()
    return {r[0] for r in rows}


def sql_annual_totals(
    conn: sqlite3.Connection, reporter: str, partner: str, flow: str, commodity: str,
    year_min: int, year_max: int,
) -> List[Dict[str, Any]]:
    """SQL GROUP BY: one value per year (totals only, real data only)."""
    rows = conn.execute(
        """WITH ranked AS (
               SELECT year, trade_value,
                      ROW_NUMBER() OVER (
                          PARTITION BY year ORDER BY retrieved_at DESC, id DESC
                      ) AS rn
               FROM trade_records
               WHERE reporter_code=? AND partner_code=? AND flow_code=? AND commodity_code=?
                 AND is_total=1 AND is_sample=? AND year BETWEEN ? AND ?
           )
           SELECT year, SUM(trade_value) AS total_value, COUNT(*) AS n_records
           FROM ranked WHERE rn = 1
           GROUP BY year
           ORDER BY year""",
        (reporter, partner, flow, commodity, sample_flag(), year_min, year_max),
    ).fetchall()
    return [dict(r) for r in rows]


def sql_yoy(
    conn: sqlite3.Connection, reporter: str, partner: str, flow: str, commodity: str,
    year_min: int, year_max: int,
) -> List[Dict[str, Any]]:
    """SQL window function: year-over-year % change, NULL when prior is missing/zero."""
    rows = conn.execute(
        """
        WITH base AS (
            SELECT year, trade_value,
                   ROW_NUMBER() OVER (
                       PARTITION BY year ORDER BY retrieved_at DESC, id DESC
                   ) AS rn
            FROM trade_records
            WHERE reporter_code=? AND partner_code=? AND flow_code=? AND commodity_code=?
              AND is_total=1 AND is_sample=? AND year BETWEEN ? AND ?
        ),
        deduped AS (
            SELECT year, trade_value FROM base WHERE rn = 1
        ),
        lagged AS (
            SELECT year, trade_value,
                   LAG(trade_value) OVER (ORDER BY year) AS prev_value
            FROM deduped
        )
        SELECT year, trade_value, prev_value,
               CASE
                 WHEN prev_value IS NULL THEN NULL
                 WHEN prev_value = 0 THEN NULL
                 ELSE ROUND((trade_value - prev_value) * 100.0 / prev_value, 2)
               END AS yoy_pct
        FROM lagged
        ORDER BY year
        """,
        (reporter, partner, flow, commodity, sample_flag(), year_min, year_max),
    ).fetchall()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------
def validate(conn: sqlite3.Connection) -> List[Dict[str, Any]]:
    """Run data-quality checks and return a list of findings."""
    issues: List[Dict[str, Any]] = []

    def add(level: str, check: str, message: str, count: int) -> None:
        issues.append({"level": level, "check": check, "message": message, "count": count})

    # Checks apply to the active mode only (real data, or sample in demo mode).
    flag = sample_flag()
    mode_name = "sample" if flag else "real"

    # 1) Duplicate totals on the uniqueness dimensions.
    dup = conn.execute(
        f"""SELECT COUNT(*) FROM (
               SELECT reporter_code, partner_code, flow_code, commodity_code,
                      year, classification, period, COUNT(*) c
               FROM trade_records WHERE is_total=1 AND is_sample={flag}
               GROUP BY reporter_code, partner_code, flow_code, commodity_code,
                        year, classification, period
               HAVING c > 1)"""
    ).fetchone()[0]
    add("error" if dup else "ok", "duplicates",
        "Duplicate total rows on the uniqueness key." if dup else "No duplicate totals.", dup)

    # 2) Missing trade values.
    missing = conn.execute(
        f"SELECT COUNT(*) FROM trade_records WHERE is_total=1 AND is_sample={flag} AND trade_value IS NULL"
    ).fetchone()[0]
    add("warning" if missing else "ok", "missing_values",
        "Total rows with a missing trade value." if missing else "No missing trade values.", missing)

    # 3) Negative or absurd values.
    neg = conn.execute(
        f"SELECT COUNT(*) FROM trade_records WHERE is_total=1 AND is_sample={flag} AND trade_value < 0"
    ).fetchone()[0]
    add("error" if neg else "ok", "negative_values",
        "Negative trade values (suspicious)." if neg else "No negative values.", neg)

    absurd = conn.execute(
        f"SELECT COUNT(*) FROM trade_records WHERE is_total=1 AND is_sample={flag} AND trade_value > 1e13"
    ).fetchone()[0]
    add("warning" if absurd else "ok", "suspicious_values",
        "Trade values above 10 trillion USD (verify)." if absurd else "No absurdly large values.", absurd)

    # 4) Exactly one total per (direction, product, year) group — the check that
    #    catches a year being counted twice (the double-counting failure mode).
    multi_total = conn.execute(
        f"""SELECT COUNT(*) FROM (
               SELECT reporter_code, partner_code, flow_code, commodity_code, year, COUNT(*) c
               FROM trade_records WHERE is_total=1 AND is_sample={flag}
               GROUP BY reporter_code, partner_code, flow_code, commodity_code, year
               HAVING c > 1)"""
    ).fetchone()[0]
    add("error" if multi_total else "ok", "single_total",
        "Groups with more than one total row." if multi_total else "Exactly one total per group.", multi_total)

    # 5) Rows belonging to the other mode are quarantined, never mixed in.
    other = conn.execute(
        f"SELECT COUNT(*) FROM trade_records WHERE is_sample={1 - flag}"
    ).fetchone()[0]
    add("info", "other_mode_isolated",
        f"{other} rows from the other data mode are quarantined and excluded from this {mode_name} view.",
        other)

    # 6) Breakdown rows present in the audit table (informational).
    breakdowns = conn.execute(
        "SELECT COUNT(*) FROM raw_records WHERE is_total = 0"
    ).fetchone()[0]
    add("info", "breakdowns_archived",
        f"{breakdowns} breakdown rows archived for audit; excluded from analysis.", breakdowns)

    return issues


def counts(conn: sqlite3.Connection) -> Dict[str, int]:
    flag = sample_flag()
    totals = conn.execute(
        f"SELECT COUNT(*) FROM trade_records WHERE is_sample={flag}"
    ).fetchone()[0]
    other = conn.execute(
        f"SELECT COUNT(*) FROM trade_records WHERE is_sample={1 - flag}"
    ).fetchone()[0]
    raw = conn.execute("SELECT COUNT(*) FROM raw_records").fetchone()[0]
    logs = conn.execute("SELECT COUNT(*) FROM ingest_log").fetchone()[0]
    return {"total_rows": totals, "sample_rows": other, "raw_rows": raw, "ingest_logs": logs}
