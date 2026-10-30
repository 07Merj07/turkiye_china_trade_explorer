# Türkiye–China Trade Explorer
## Data Contract and MVP Implementation Plan

**Status:** Agreed MVP decisions  
**Data source:** UN Comtrade  
**Currency displayed:** USD  
**Team:** Mert (data, SQL, validation, analytics) and Tao (API, UI, integration)

## 1. Purpose

Türkiye–China Trade Explorer is a web application for exploring annual merchandise trade between Türkiye and China by product and year range.

Users can search by product name in Turkish, English, or Chinese, or by HS code; choose a trade direction; select a start and end year from 2010 through the latest available year; and view annual values, year-over-year change in USD and percent, a line chart, and a compact annual values table.

The app must not imply that unavailable data means zero trade. It must not claim trade value alone predicts profitability or demand.

## 2. Agreed MVP decisions

1. Interface language: English.
2. Search: Turkish, English, Chinese product names, and HS code.
3. Catalogue: use a broad HS product catalogue where possible; do not limit the app to only 100–200 products. Aliases must map to verified HS codes.
4. Search results: show categories and sub-products. If several matches exist, show product name and HS code for the user to choose.
5. Trade directions: Türkiye → China (Türkiye-reported exports to China) and China → Türkiye (China-reported exports to Türkiye).
6. Period: start-year and end-year selectors; period begins in 2010 and ends at the latest year available for the specific query.
7. Chart: one line chart, with exact values on chart interaction and a small annual-value table underneath.
8. Currency: USD only.
9. Year-over-year change: show both absolute USD change and percentage change.
10. Missing values: display `No data`; do not replace missing values with zero.
11. If the immediately previous calendar year's value is unavailable, display `N/A` for year-over-year change.
12. Source display: show source, year, HS code, and measure in a compact line below the chart. Add a short Data Source & Methodology section to the README.
13. No CSV/Excel download in the MVP.
14. Do not retain search history.
15. No scheduled automatic refresh initially; refresh data when needed.
16. If the API fails, show an error message; no automatic retry system in the MVP.
17. If no product match is found, show a message and suggest similar product names or HS codes when possible.
18. If there is no data for the selected period, show `No data available for this period.`
19. Shared database: use an online database such as Supabase, not a production dataset stored on either developer's computer.
20. Data flow: if a requested record is missing, the server fetches it from UN Comtrade, validates it, stores it, and returns it. Later searches can use the stored record.
21. Store annual totals first; detailed API breakdowns are out of scope for the MVP.
22. Unique record key: product HS code + trade direction + year.
23. If a new value arrives for an existing key, update the existing record rather than creating a duplicate.
24. Store the source name and the date/time the data was retrieved.
25. Only the server-side application can write/update records. End users must not write directly to the database.

## 3. Data interpretation rules

### Trade direction
The selected direction must map to the correct reporter, partner, and flow parameters in the UN Comtrade request. The two directions are not interchangeable. Mirror-import comparisons are out of scope for the MVP.

### CIF and FOB
Use the direction-appropriate main measure:
- Imports: CIF where available.
- Exports: FOB where available.

If the selected measure is unavailable, do not invent or estimate it. Mark the value/measure unavailable unless a documented and validated fallback is agreed. Do not add CIF and FOB together; they are alternative valuation measures.

### Totals and double counting
UN Comtrade responses can contain total rows and breakdown rows. Never sum a total together with its sub-breakdowns. Define and test exact filters for the correct total row before storing annual totals. A successful query for one product/year does not validate the same filters for every product, year, direction, or classification.

### Missing data and annual change
- Missing data is not zero.
- If year `t` is missing, show `No data`.
- Calculate year-over-year change only when both `t` and immediately preceding calendar year `t-1` have valid values.
- Absolute change = `value_t - value_(t-1)`.
- Percentage change = `((value_t - value_(t-1)) / value_(t-1)) * 100`, only when the previous value is valid and nonzero.
- If the previous year's value is missing, show `N/A`.
- If the previous value is zero, percentage change is undefined; show `N/A` for percentage change.

### Latest year
Do not assume the latest calendar year is complete. Availability can vary by product, direction, and year. Display only actual returned values and appropriate missing-data states.

## 4. Application-level data contract

These are application field names, not necessarily the exact source API field names. Mert and Tao should agree on the source-to-application mapping before implementation.

| Field | Type | Meaning |
|---|---|---|
| `product_code` | text | HS code; use text to preserve leading zeros |
| `product_name` | text | Canonical English product/category name |
| `reporter_code` | text | Country reporting the trade record |
| `partner_code` | text | Trade partner code |
| `trade_direction` | enum/text | `TURKEY_TO_CHINA` or `CHINA_TO_TURKEY` |
| `year` | integer | Calendar year |
| `trade_value_usd` | numeric/decimal | Validated annual total in USD |
| `trade_measure` | text | Actual measure used, such as `CIF` or `FOB` |
| `source_name` | text | `UN Comtrade` |
| `retrieved_at` | timestamp with time zone | When the value was retrieved/validated |
| `classification` | text | HS classification/version |
| `source_query_params` | JSON, optional | Useful for auditing/debugging |

Product aliases should be kept separately, e.g. `alias`, `language` (`tr`, `en`, `zh`), and `product_code`. A broad category may map to several sub-products; do not assign a random code or treat a broad category as one product unless its aggregation is explicitly defined.

## 5. Suggested Supabase tables

### `products`
- `product_code` (text; unique, or unique with classification/version if needed)
- `product_name_en` (text)
- `parent_product_code` (text, nullable)
- `classification` (text)
- `is_active` (boolean)

### `product_aliases`
- `id` (primary key)
- `alias` (text)
- `language` (text: `tr`, `en`, `zh`)
- `product_code` (foreign key to `products`)

Index aliases for search. If an alias matches multiple products, show choices instead of selecting randomly.

### `annual_trade_values`
- `product_code` (foreign key)
- `trade_direction` (text)
- `year` (integer)
- `trade_value_usd` (numeric/decimal)
- `trade_measure` (text, e.g. `CIF` or `FOB`)
- `source_name` (text)
- `retrieved_at` (timestamp with time zone)
- `source_reporter_code` (text)
- `source_partner_code` (text)
- `classification` (text)
- `source_query_params` (JSON, optional)
- unique constraint: (`product_code`, `trade_direction`, `year`)

If HS classification versions differ across years, include the version in the product identity or document how codes are harmonized. Do not silently assume every code has the same meaning across all versions.

## 6. Request and caching flow

1. User enters a product name or HS code.
2. Server searches the product/alias catalogue.
3. If multiple products match, UI shows category/sub-product choices with HS codes.
4. User selects a product, direction, start year, and end year.
5. Server checks `annual_trade_values` for the requested range.
6. For missing records, server requests data from UN Comtrade.
7. Server validates metadata, chooses the correct total row, checks the measure, and prevents double counting.
8. Server upserts the annual total using the unique key. New values update existing records.
9. Server returns values and metadata to the UI.
10. UI displays the line chart, annual table, year-over-year changes, and compact source information.

The server should distinguish: no product match, ambiguous product match, valid query with no data, API/network error, invalid/unsupported query, and available data.

Do not expose Supabase service-role credentials or secrets in browser code. Enforce permissions so end users cannot write directly to the database.

## 7. Responsibilities

### Mert — data, SQL, validation, analytics
- Prepare the data dictionary and source-field mapping.
- Design tables, keys, constraints, and indexes.
- Validate total-row selection and prevent double counting.
- Write SQL queries for annual values and year-over-year changes.
- Test missing values, duplicates, direction-specific measures, and update behavior.
- Prepare chart/table data and document source, valuation, and limitations.

### Tao — API, UI, integration
- Implement the UN Comtrade API client and parameter mapping.
- Handle API responses, empty results, errors, and rate limits.
- Build product search, match choices, direction selector, and year selectors.
- Implement server-side reads/writes to Supabase.
- Integrate Mert's query results and chart data.
- Help deploy after local tests pass.

### Shared
- Agree on exact field mappings and query parameters before integration.
- Test representative products, both directions where available, and several years.
- Verify chart, table, and annual-change calculations agree.
- Prepare README and deployment instructions.

## 8. Implementation order

1. Agree on field names/types, direction mapping, and total-record selection rules.
2. Validate a small sample: one product code and several years, testing both directions where data exists.
3. Create Supabase tables, unique constraints, indexes, and access policies.
4. Implement server-side API ingestion and upsert.
5. Implement SQL queries for annual values, missing years, and annual change.
6. Build UI: search, product match selection, direction, year range, line chart, table, source line.
7. Test no match, multiple matches, missing year, missing previous year, API failure, repeated query, updated source value, and invalid year range.
8. Deploy after local integration and access policies are tested (e.g. Vercel for the web app and Supabase for the database).
9. Document source, CIF/FOB choice, missing-data handling, HS limitations, and setup instructions.

## 9. MVP acceptance checklist

- [ ] Search by HS code and supported aliases works.
- [ ] Turkish, English, and Chinese aliases work for entries actually included in the catalogue.
- [ ] Multiple matches show selectable product names and HS codes.
- [ ] Both directions map to the correct reporter/partner/flow.
- [ ] User can select a valid year range.
- [ ] Annual values use validated total records, without summing totals and breakdowns.
- [ ] Chart and table show the same values.
- [ ] Annual USD and percentage changes use the immediately previous calendar year.
- [ ] Missing data is not shown as zero.
- [ ] Source, year, HS code, and measure are visible.
- [ ] Repeated queries do not create duplicate records.
- [ ] Updated values replace existing values for the same product/direction/year.
- [ ] API failures show a clear error.
- [ ] End users cannot write directly to the database.
- [ ] Secrets are not committed to GitHub.

## 10. Out of scope for MVP

- CSV/Excel download
- Search history
- Scheduled automatic refresh
- AI-powered product matching
- Comparing mirror exports/imports from both reporting countries
- Forecasting, demand prediction, or profitability recommendations
- Detailed customs/transport/second-partner breakdowns
- Comparing multiple products in one chart
- Multiple chart types
- Conversion to TRY or CNY

## 11. Limitations to state honestly

- Broad categories can represent several HS codes; aggregation must avoid overlapping totals.
- A multilingual alias catalogue requires preparation; the app does not promise perfect matching for every possible product name.
- Data availability and completeness vary by product, direction, classification, and year.
- `retrieved_at` records when the app last retrieved data; it does not prove that source data is complete.
- Check current UN Comtrade terms and Supabase/Vercel limits before public launch.
- Total-row selection must be validated across representative queries; one successful query does not prove every query is correct.

## Plain-language summary

The user searches for a product. The app finds the matching HS code, checks Supabase, and if the annual value is missing, asks UN Comtrade for it. The server validates the correct total, stores it under product + direction + year, and returns it for the chart and table. Missing data is shown as missing, not zero. Mert owns SQL/data validation/analysis; Tao owns API/UI/integration; both agree the field mapping and test the complete flow.
