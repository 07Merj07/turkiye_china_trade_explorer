# Türkiye--China Trade Explorer

## Team Responsibilities, Product Scope, and Step-by-Step Development Plan

**Team:** Mert (Türkiye) and Tao (China)\
**Initial data source:** UN Comtrade / Comtrade Plus\
**Goal:** Build a reliable trade-data exploration application, validate
it with real queries, and expand only after the core workflow works.

## 1. Project Goal

Users should be able to search for a product, choose a trade direction
and period, inspect annual trade values, and understand changes over
time. The MVP is a trade-data exploration tool; it must not claim to
predict profitability, consumer demand, or future sales from trade
statistics alone.

## 2. Agreed Product Scope

### Countries and directions

Support both directions: - **Türkiye → China:** Türkiye's exports to
China; China's corresponding imports may be shown as a separate
reporting perspective. - **China → Türkiye:** China's exports to
Türkiye; Türkiye's corresponding imports may be shown as a separate
reporting perspective.

Always label the reporting country, partner country, and trade flow.
Mirror records may differ because of CIF/FOB valuation, reporting
timing, coverage, classification, and national reporting practices. Do
not force the two sides to match.

### Products

The target scope is broad: textiles, lamps, electronics, and other
merchandise products, using HS classifications where appropriate.

For the MVP: - Search by product name or HS code. - Use an HS/product
reference catalogue. - If a product name matches multiple codes, show
options instead of silently choosing an uncertain match. - Do not
promise perfect free-text understanding in every language from day
one. - Record the HS classification/version used because classifications
can change.

### Years

**Recommended starting range: 2010 through the latest year available for
the selected query.**

A record was returned for 2025 in the initial test, but this does not
prove that every product, direction, and reporting country has complete
2025 data. Check availability per query. Missing data must not
automatically be treated as zero.

### Currency and valuation

Display values in **USD**, subject to the metadata for the relevant
dataset and year. The metadata inspected by the team listed USD and
described import valuation as CIF/FOB and export valuation as FOB.

-   **CIF:** Goods' transaction value plus relevant transport and
    insurance costs to the importing country's border.
-   **FOB:** Goods' transaction value plus relevant costs to the
    exporting country's border.
-   **`primaryValue`:** The source documentation says it prioritizes
    CIF-type values and uses FOB-type values where applicable.

Show the value type where possible and explain that import/export values
may differ because of valuation and reporting practices.

### Source disclosure

Show the source near charts/results, for example:

> Source: UN Comtrade. Availability and values depend on
> reporting-country submissions and may be revised. Import and export
> records may differ because of valuation and reporting practices.

Create a **Data & Methodology** page/section explaining: - Source and
link. - Reporting country, partner, flow, product code, and period. -
Retrieval/refresh date. - Currency and valuation fields used. -
Missing-data handling. - Product-code matching limitations. - Known
limitations.

If more sources are added later, preserve source information for each
dataset/record.

### CSV downloads

**Do not include raw CSV downloads in the initial MVP.** Check UN
Comtrade's applicable data-use and redistribution rules before offering
downloads. Changing format or renaming columns does not automatically
make raw data transformed or exempt from redistribution restrictions.
The first release can display charts and analytical results in the app;
revisit downloads after the applicable terms are confirmed.

## 3. MVP Features

### Required

1.  **Product search:** Search by product name or HS code; show options
    for ambiguous matches; display the selected HS code.
2.  **Trade-direction selection:** Türkiye → China and China → Türkiye,
    with reporting country, partner, and flow clearly labelled.
3.  **Year selection:** 2010 through the latest year available for the
    specific query; missing years must be visible.
4.  **Annual trade-value chart:** Annual values for the selected product
    and direction, with clear currency/units.
5.  **Year-over-year change:** Percentage change when both years have
    valid values; handle zero/missing prior values explicitly.
6.  **Trade-direction comparison:** Allow users to inspect both
    directions, without implying mirror records must match.
7.  **Source/methodology information:** Source, retrieval date,
    valuation, and limitations.

### Defer until later

-   Profitability or consumer-demand prediction.
-   Machine-learning forecasts.
-   Complex AI matching across all languages.
-   Many extra charts/maps.
-   Raw CSV downloads until redistribution permissions are clear.
-   Additional data sources until the first pipeline is reliable.

## 4. Team Responsibilities

### Mert --- Data, SQL, analysis, and visualizations

Mert owns data correctness and analytical outputs.

Responsibilities: 1. Inspect API responses and maintain a data
dictionary. 2. Design database tables and relationships. 3. Define a
uniqueness rule after confirming which dimensions identify an
observation. 4. Write SQL queries by product, year, reporting country,
partner, and flow. 5. Prevent double counting by separating totals from
detailed breakdowns. 6. Check duplicates, missing/zero values,
classification versions, units, and suspicious values. 7. Compare
Türkiye-reported and China-reported mirror records and document
differences. 8. Calculate annual totals and year-over-year changes. 9.
Build Plotly charts and check that chart values match query results. 10.
Explain analytical limitations and help write methodology documentation.

**Mert's deliverables:** data dictionary; proposed database schema; SQL
scripts/queries; validation checklist and results; analysis outputs;
Plotly code; explanations of metrics and limitations.

### Tao --- API integration and application interface

Tao owns programmatic data retrieval and the user-facing application.

Responsibilities: 1. Build Python functions to call the UN Comtrade API
with explicit parameters. 2. Preserve the exact query parameters for
each response. 3. Handle API errors, empty responses, rate limits, and
missing fields. 4. Convert API responses to the agreed format. 5.
Integrate ingestion with the database schema agreed with Mert. 6. Build
product search, direction selection, and year selection. 7. Integrate
Mert's charts and analytical outputs into the UI. 8. Show clear messages
for missing data and API failures. 9. Prepare local run steps and later
deployment. 10. Document setup and execution.

**Tao's deliverables:** API-fetching code; example response and query
parameters; ingestion code; initial UI; integration; error handling;
setup instructions.

### Shared responsibilities

Both should agree on MVP scope and the data contract; review HS
mappings; agree on the meaning of reporting country, partner, flow, and
valuation; investigate unexpected differences; test the complete user
journey; review code; and maintain accurate README/methodology notes.

## 5. Dependencies: What Each Person Needs

### Tao → Mert

Tao should provide: - A representative JSON response. - Exact API
parameters used to obtain it. - Returned field names and types. - Any
API limitations, errors, or missing-field behaviour.

Mert can start with the existing JSON and draft the schema immediately.
Validate it against Tao's programmatic response before finalizing.

### Mert → Tao

Mert should provide: - Agreed table and field definitions. - Rules
distinguishing totals from breakdowns. - Expected query-result format. -
Fields required by each chart. - Metric definitions and rules for
missing values/uncertain HS matches.

Tao can build the API client and a basic UI in parallel, but should not
create a conflicting database schema.

### Shared data contract

Agree on field names, types, meanings, and the shape of a query result.
This prevents SQL and chart code from expecting a different format from
the API client.

## 6. Step-by-Step Plan

### Step 1 --- Agree on scope (together)

Confirm countries/directions, product search, year range, USD/source
display, no raw CSV downloads in MVP, and included/excluded features.
**Output:** Short scope document.

### Step 2 --- Work in parallel on the data contract

**Mert:** Inspect the existing 272-row JSON, document needed fields,
draft schema and candidate uniqueness rule, identify relevant
dimensions.\
**Tao:** Write a Python request for the known query, save exact
parameters, and provide the response.\
**Output:** Draft schema and reproducible API response.

### Step 3 --- Confirm core query and total rules

Run a narrow query for one product, year, reporting country, partner,
and flow. Compare it with the existing JSON. Check second-partner,
customs, and transport dimensions. Document how to select the intended
total. **Important:** The initial 2023 query returned one row matching
the candidate total in the JSON; the same query structure returned one
row for 2025. This validates those specific queries only, not every
product, year, or flow. Never sum all records in a multi-dimensional
response blindly. **Output:** Repeatable, documented query for one
total.

### Step 4 --- Create the database

**Mert leads; Tao reviews compatibility.** Create initial tables, define
a uniqueness rule based on the actual dimensions, preserve
source/query/classification/flow/partner/valuation information, load a
sample, and run basic SQL queries. **Output:** Local database with
sample records and tested queries.

### Step 5 --- Automate ingestion

**Tao leads; Mert validates.** Fetch data, validate response shape, load
it into the agreed schema, prevent duplicate inserts on reruns, preserve
query/retrieval metadata, and handle missing data/API errors.
**Output:** Repeatable API-to-database workflow.

### Step 6 --- Build and validate analysis queries

**Mert leads.** Query annual values, calculate valid year-over-year
changes, distinguish missing data from true zero, test multiple years
and products, compare mirror records without assuming they match, and
document remaining differences. **Output:** SQL queries and analysis
results for charts.

### Step 7 --- Build charts

**Mert leads.** Create an annual trade-value line chart, trade-direction
comparison, and year-over-year change chart. Label values, units, and
missing-data behaviour. Start with sample data, then connect charts to
real query results. **Output:** Reusable Plotly charts with defined
input fields.

### Step 8 --- Build and integrate the UI

**Tao leads; Mert supports.** Add product search, HS selection,
direction/year filters, connect the data workflow, display values and
charts, show source/methodology, and handle missing results/errors.
**Output:** Working end-to-end application.

### Step 9 --- Test the complete application

**Together.** Test product-name and HS-code search, both directions,
several years, missing data, source-vs-SQL values, double counting,
chart labels/currency, API errors/rate limits, and confirm no raw
download feature is exposed unless permitted. **Output:** Test results,
known limitations, and remaining issues.

### Step 10 --- Document and prepare to share

**Together.** Write README, source/methodology/limitations, setup
instructions, and screenshots after the UI works. Keep secrets out of
the repository and review licensing/deployment choices. **Output:**
Reproducible GitHub project ready for review.

## 7. Initial Findings --- Not Full Validation

The team has already observed: - The supplied JSON had 272 records and
47 fields. - A narrow 2023 query returned one record matching the
candidate total in the JSON. - The same query structure for 2025
returned one record. - The inspected metadata listed USD and described
import valuation as CIF/FOB and export valuation as FOB. - The wider
JSON included multiple customs, transport, and second-partner
breakdowns; summing all rows would be unsafe.

These are useful initial checks, **not proof that all data is correct**.
Further validation is required across products, years, and reporting
perspectives.

## 8. First-Day Checklist

### Mert

-   [ ] Review the existing JSON and start the data dictionary.
-   [ ] Draft the first database schema.
-   [ ] Define fields needed by the annual chart.
-   [ ] Build a small Plotly prototype using sample values.
-   [ ] Write down total-selection and double-counting rules.

### Tao

-   [ ] Write a Python API request for the known test query.
-   [ ] Save the exact query parameters and response.
-   [ ] Handle errors and empty results.
-   [ ] Draft the basic UI.
-   [ ] Review Mert's field names before finalizing ingestion.

### Together

-   [ ] Agree on MVP scope.
-   [ ] Agree on field names and data types.
-   [ ] Confirm how each trade direction is represented.
-   [ ] Add the scope and data contract to the shared repository.
-   [ ] Review the first end-to-end query before expanding to more
    products.

## 9. Working Principles

1.  Explain important decisions and why they are needed.
2.  Do not hide uncertainty in values or product matches.
3.  Do not sum blindly; distinguish totals from breakdowns.
4.  Do not assume mirror records match; compare and explain differences.
5.  Build in small, testable steps.
6.  Keep data/analysis separate from presentation.
7.  Preserve source, query dimensions, classification, and retrieval
    details.
8.  Keep the MVP achievable and add advanced features only after the
    core workflow works.

## 10. Definition of MVP Success

The MVP succeeds when a user can: 1. Search for a supported product or
HS code. 2. Select Türkiye → China or China → Türkiye. 3. Choose an
available year/period. 4. See annual values and valid year-over-year
changes. 5. View clearly labelled charts. 6. Identify the source and key
limitations. 7. Get a clear message when data is unavailable.

The first version does not need to predict profitability or perfectly
understand every product phrase. Its job is to provide a clear,
traceable, responsibly interpreted view of trade data.
