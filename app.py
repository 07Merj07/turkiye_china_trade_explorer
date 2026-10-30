"""
Türkiye–China Trade Explorer
Neon PostgreSQL + Streamlit MVP

Run with: streamlit run app.py
"""

import pandas as pd
import streamlit as st

import analysis
import charts
import database_neon as database


DIRECTIONS = {
    "TR_TO_CN": {
        "label": "Türkiye → China",
        "description": "Türkiye-reported exports to China",
        "reporter": "TUR",
        "partner": "CHN",
    },
    "CN_TO_TR": {
        "label": "China → Türkiye",
        "description": "China-reported exports to Türkiye",
        "reporter": "CHN",
        "partner": "TUR",
    },
}

YEAR_MIN = 2019
YEAR_MAX = 2025

st.set_page_config(
    page_title="Türkiye–China Trade Explorer",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown("""
<style>
div[data-testid="stAppViewBlockContainer"] {
    padding-top: 4rem !important;
}
</style>
""", unsafe_allow_html=True)

st.markdown(
    """
    <style>
        .block-container {padding-top: 2rem; padding-bottom: 2rem;}
        .app-title {font-size: 2rem; font-weight: 700; margin-bottom: 0;}
        .app-sub {color: #9aa4b2; font-size: .95rem; margin-top: .2rem;}
        .foot {color: #6b7480; font-size: .78rem; margin-top: 2rem;}
    </style>
    """,
    unsafe_allow_html=True,
)


def load_direction(direction_key, commodity, year_min, year_max,
                   progress=None, progress_value=1.0):
    """Read one direction's annual trade series from Neon."""
    records = database.fetch_direction_series(
        direction_key=direction_key,
        commodity=commodity,
        year_min=year_min,
        year_max=year_max,
    )
    if progress is not None:
        progress.progress(
            progress_value,
            text=f"{DIRECTIONS[direction_key]['label']}: "
                 f"{len(records)} annual records loaded",
        )
    return records


# Sidebar: product search
st.sidebar.header("Search")
query = st.sidebar.text_input(
    "Product name or HS code",
    value="lamps",
    help="Search the Neon product catalogue by English description or HS code.",
)

try:
    matches = database.search_products(query, limit=50)
except Exception as exc:
    st.error(f"Could not search the Neon product catalogue: {exc}")
    st.stop()

selected_entry = None
if not matches:
    st.sidebar.warning("No product matched. Try another English name or HS code.")
else:
    labels = [
        (
            f"{item['code']} — {item['name']} · {item['hs_version']} · "
            f"{'Leaf product' if item['is_leaf'] else 'Parent group'}"
        )
        for item in matches
    ]
    if len(matches) == 1:
        selected_entry = matches[0]
        st.sidebar.caption(f"Matched: {labels[0]}")
    else:
        st.sidebar.caption(
            f"{len(matches)} matches shown. Choose the exact product; "
            "the app does not guess."
        )
        selected_label = st.sidebar.selectbox("Select product", labels)
        selected_entry = matches[labels.index(selected_label)]

    if len(matches) == 50:
        st.sidebar.caption("Showing up to 50 matches. Refine your search if needed.")

st.sidebar.divider()
direction_key = st.sidebar.radio(
    "Trade direction",
    options=list(DIRECTIONS.keys()),
    format_func=lambda key: DIRECTIONS[key]["label"],
)
st.sidebar.caption(DIRECTIONS[direction_key]["description"])

year_min, year_max = st.sidebar.slider(
    "Year range",
    min_value=YEAR_MIN,
    max_value=YEAR_MAX,
    value=(YEAR_MIN, YEAR_MAX),
    step=1,
)
compare = st.sidebar.checkbox(
    "Compare both directions",
    value=False,
    help="Also load the other reporting country's export series.",
)
st.sidebar.divider()
st.sidebar.caption(
    "Values are in USD. Export records are filtered to FOB valuation. "
    "Missing years are shown as gaps, not as zero."
)


# Header
st.markdown(
    '<p class="app-title">🌐 Türkiye–China Trade Explorer</p>',
    unsafe_allow_html=True,
)
st.markdown(
    '<p class="app-sub">Explore annual merchandise exports between '
    'Türkiye and China by HS product, reporting direction and year. '
    'Data is read from the project Neon PostgreSQL database.</p>',
    unsafe_allow_html=True,
)

if selected_entry is None:
    st.info("Choose a product from the sidebar to begin.")
    st.stop()

commodity = selected_entry["code"]
commodity_desc = selected_entry["name"]
commodity_label = f"{commodity} — {commodity_desc}"

st.caption(
    f"Product: **{commodity_label}** · "
    f"Catalogue version: **{selected_entry['hs_version']}** · "
    f"Parent HS code: **{selected_entry['parent_hs_code'] or 'None'}** · "
    f"Level: **{selected_entry['aggregation_level']}**"
)


# Load data from Neon
progress = st.progress(0.0, text="Loading data from Neon…")
try:
    primary_raw = load_direction(
        direction_key, commodity, year_min, year_max,
        progress=progress,
        progress_value=0.5 if compare else 1.0,
    )

    if compare:
        other_key = "CN_TO_TR" if direction_key == "TR_TO_CN" else "TR_TO_CN"
        other_raw = load_direction(
            other_key, commodity, year_min, year_max,
            progress=progress, progress_value=1.0,
        )
    else:
        other_raw = []
except Exception as exc:
    progress.empty()
    st.error(f"Could not load trade data from Neon: {exc}")
    st.stop()
progress.empty()

primary_series = analysis.annual_series(primary_raw)
other_series = analysis.annual_series(other_raw)
primary_metrics = analysis.summary_metrics(primary_series)
primary_yoy = analysis.yoy_changes(primary_series)

st.success("Connected to Neon PostgreSQL · Showing stored database records.")


# KPI cards
latest_yoy = next(
    (item for item in reversed(primary_yoy) if item["pct"] is not None),
    None,
)

if not primary_series:
    st.warning(
        "No records were found for this product, direction and year range. "
        "Missing data is not treated as zero."
    )
else:
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric(
            f"Latest value ({primary_metrics['last_year']})",
            analysis.format_usd(primary_metrics["latest_value"]),
            delta=(
                f"{latest_yoy['pct']:+.1f}% YoY"
                if latest_yoy else "No valid prior-year comparison"
            ),
        )
    with c2:
        st.metric(
            f"Total {year_min}–{year_max}",
            analysis.format_usd(primary_metrics["total"]),
            help="Sum of the available annual values in the selected period.",
        )
    with c3:
        st.metric(
            "CAGR",
            (
                f"{primary_metrics['cagr']:+.1f}%"
                if primary_metrics["cagr"] is not None else "n/a"
            ),
            help="Compound annual growth rate between the first and last available years.",
        )
    with c4:
        peak = primary_metrics["peak"]
        st.metric(
            "Peak year",
            str(peak["year"]) if peak else "n/a",
            delta=analysis.format_usd(peak["value"]) if peak else None,
        )

direction = DIRECTIONS[direction_key]
st.caption(
    f"Reporting country: **{direction['reporter']}** · "
    f"Partner country: **{direction['partner']}** · "
    "Flow: **Exports (X)** · Valuation: **FOB**"
)


# Tabs
tab_trend, tab_yoy, tab_compare, tab_data, tab_method = st.tabs(
    ["📈 Trend", "📊 Year-over-year", "🔀 Comparison", "🗂 Data", "📚 Methodology"]
)

with tab_trend:
    if not primary_series:
        st.info("No annual data is available for this selection.")
    else:
        fig = charts.annual_value_line(
            primary_series,
            title=f"Annual trade value — {commodity_label}",
            direction_label=direction["label"],
            valuation="FOB",
        )
        st.plotly_chart(fig, width="stretch")
        st.subheader("How to read this chart")
        for note in analysis.interpret(
            primary_series, direction["label"], commodity_label, valuation="FOB"
        ):
            st.markdown(f"- {note}")

with tab_yoy:
    if not primary_series:
        st.info("No annual data is available for this selection.")
    else:
        fig = charts.yoy_bar(
            primary_yoy,
            title=f"Year-over-year change — {commodity_label}",
        )
        st.plotly_chart(fig, width="stretch")

        status_labels = {
            "ok": "Valid",
            "no_prior_year": "No prior-year data (gap)",
            "prior_zero": "Prior value was zero (undefined)",
            "missing_value": "Missing value",
        }
        yoy_df = pd.DataFrame([
            {
                "Year": item["year"],
                "Value (USD)": item["value"],
                "Previous year (USD)": item["prev_value"],
                "Change (%)": (
                    round(item["pct"], 2) if item["pct"] is not None else None
                ),
                "Status": status_labels.get(item["status"], item["status"]),
            }
            for item in primary_yoy
        ])
        st.dataframe(yoy_df, width="stretch", hide_index=True)
        st.caption(
            "A percentage is calculated only when the previous calendar year "
            "has a valid, non-zero value."
        )

with tab_compare:
    st.markdown(
        f"Comparing **{DIRECTIONS['TR_TO_CN']['label']}** and "
        f"**{DIRECTIONS['CN_TO_TR']['label']}** for {commodity_label}. "
        "These are separate reporting perspectives and are not expected "
        "to match exactly."
    )
    if not compare:
        st.info(
            "Enable 'Compare both directions' in the sidebar to load "
            "the other reporting country's export data."
        )
    elif not primary_series and not other_series:
        st.info("No comparison data is available for this selection.")
    else:
        if direction_key == "TR_TO_CN":
            turkey_series, china_series = primary_series, other_series
        else:
            china_series, turkey_series = primary_series, other_series

        rows = analysis.compare_directions(turkey_series, china_series)
        log_scale = st.toggle(
            "Logarithmic scale",
            value=False,
            help="Useful when the two trade values differ substantially.",
        )
        fig = charts.direction_comparison(
            rows,
            DIRECTIONS["TR_TO_CN"]["label"],
            DIRECTIONS["CN_TO_TR"]["label"],
            log_scale=log_scale,
        )
        st.plotly_chart(fig, width="stretch")

        fig_balance = charts.balance_chart(
            rows,
            DIRECTIONS["TR_TO_CN"]["label"],
            DIRECTIONS["CN_TO_TR"]["label"],
        )
        st.plotly_chart(fig_balance, width="stretch")
        st.caption(
            "Balance = Türkiye-reported exports to China minus "
            "China-reported exports to Türkiye."
        )

with tab_data:
    st.subheader("Annual trade values")
    if primary_series:
        data_df = pd.DataFrame([
            {"Year": item["year"], "Trade value (USD)": item["value"]}
            for item in primary_series
        ])
        st.dataframe(data_df, width="stretch", hide_index=True)
    else:
        st.info("No rows to display.")

    available_years = {item["year"] for item in primary_series}
    missing_years = [
        year for year in range(year_min, year_max + 1)
        if year not in available_years
    ]

    st.subheader("Data availability")
    st.write(f"Available annual records: **{len(primary_series)}**")
    if missing_years:
        st.warning(
            "No record was returned for these years: "
            + ", ".join(map(str, missing_years))
            + ". They are left blank, not converted to zero."
        )
    else:
        st.success("A record is available for every year in the selected range.")

    st.caption(
        "The SQL query checks for multiple records for the same product, "
        "direction and year. If duplicates are found, it stops rather than "
        "silently summing or selecting one."
    )

with tab_method:
    st.subheader("Data & Methodology")
    st.markdown(
        """
**Database.** Data is read from the project's Neon PostgreSQL database.

**Source.** Stored trade records originate from UN Comtrade data imported
into this project. Values depend on reporting-country submissions and may
be revised by the source.

**Trade direction.** Each direction is based on the reporting country,
partner country and export flow (`X`). Türkiye → China uses reporter `TUR`
and partner `CHN`; China → Türkiye uses reporter `CHN` and partner `TUR`.

**Valuation.** The application filters export records to FOB valuation
(Free on Board).

**Currency.** The annual query uses records whose currency is USD.

**Missing data.** If a year has no matching record, it is displayed as a gap,
not as zero.

**Duplicate protection.** If more than one matching record exists for the
same product, direction and year, the query raises an error. The application
does not silently sum potentially overlapping records.

**Classification limitation.** Trade records use H5 for 2019–2021 and H6
for 2022–2025. The product catalogue is based on HS2022. Historical code
equivalence is not guaranteed for every product; HS concordance must be
checked before treating every historical code as perfectly comparable.

**Mirror records.** Values reported by Türkiye and China may differ because
of reporting coverage, timing, valuation and classification practices.
The application does not force the two reporting perspectives to match.

**Scope.** This is a historical trade-data exploration tool. It does not
forecast future trade or estimate product profitability.
        """
    )

st.markdown(
    '<p class="foot">Türkiye–China Trade Explorer · MVP · '
    'Database: Neon PostgreSQL · Source data: UN Comtrade</p>',
    unsafe_allow_html=True,
)
