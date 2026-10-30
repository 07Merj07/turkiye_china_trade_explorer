# Türkiye–China Trade Explorer
## AI Handoff Brief — Current MVP Specification

**Purpose:** This is the current, concise source of truth for implementing the MVP. Read it before proposing or writing code.

**Team:** Mert (data, SQL, validation, analysis) and Tao (API integration, UI, application integration).

**Project status:** Planning and validation. Do not assume that the complete application already exists or that every API rule has been validated.

---

## 1. How to treat this document

- Treat the decisions explicitly marked **MVP decision** as the current product requirements.
- Treat items marked **To validate** as unresolved technical questions, not established facts.
- If an older document conflicts with this brief, follow this brief unless Mert and Tao explicitly agree to change it.
- Do not invent API fields, database schemas, successful test results, or data values.
- Before coding a major component, explain the approach, why it is needed, assumptions, and tests.
- Keep the implementation small and testable. Do not add features outside the MVP without asking.

## 2. Product goal

Build a simple English-language web application that lets a user search for a merchandise product, choose its official HS product category, select a Türkiye–China trade direction and year range, and inspect annual trade values and changes.

The app helps users explore reported trade statistics. It must not claim that trade value alone proves consumer demand, profitability, or future sales.

## 3. MVP decisions

### Geography and language
- Only Türkiye and China.
- User interface language: English.
- Product search should support Turkish, English, and Chinese names when those names or aliases exist in the catalogue.
- Also allow search by HS code.
- Do not promise perfect recognition of every phrase.

### Product search
- Use a broad official HS/product classification catalogue where practical; do not manually limit the app to a tiny hand-written list.
- Keep the product catalogue separate from annual trade values.
- Support broad categories and more detailed sub-products.
- Show product name and HS code in search results.
- If several products may match, let the user choose; never silently force an uncertain match.
- If no match exists, show a clear message and suggest alternatives when possible.
- Store HS codes as text to preserve leading zeros.
- Store the classification and version because HS codes can change meaning across versions.

### Trade direction
Show two choices:

1. `TURKEY_TO_CHINA`: Türkiye-reported exports to China.
2. `CHINA_TO_TURKEY`: China-reported exports to Türkiye.

For each direction, map reporter, partner, and flow parameters explicitly. Always label the reporting perspective. The two countries' mirror records may differ and must not be forced to match.

### Years and values
- Allow start-year and end-year dropdowns.
- Start at 2010 and extend to the latest year available for the particular query, without implying the latest calendar year is complete.
- Reject a start year later than the end year.
- Display USD only in the MVP.
- Main screen: one line chart, a compact annual values table, and year-over-year change in USD and percent.
- Exact annual value should appear on chart hover/tap where supported.
- No multi-product comparison in the MVP.
- No CSV/Excel download, search history, scheduled refresh, forecasting, or profitability predictions in the MVP.

### Missing values and changes
- Missing data is not zero.
- Show `No data` for a missing year and leave a gap in the chart.
- If the immediately previous calendar year is missing, show `N/A` for year-over-year change; do not compare with the nearest available year.
- Absolute change = current year value − previous calendar year value.
- Percentage change = `(current − previous) / previous × 100`.
- If the previous value is missing or zero, percentage change is `N/A`.

### Source and errors
- Display a compact source line including source, year, HS code/classification where relevant, and actual valuation measure.
- README must have a concise Data Source & Methodology section.
- If no trade data exists for the selected period, show `No data available for this period.` Do not represent this as zero trade.
- API errors should produce a clear user-facing error. Automatic retries are not required in the MVP.
- No automated background refresh. Fetch missing data when requested and cache validated results.

## 4. Data source and valuation

Primary source: UN Comtrade / Comtrade Plus.

General intended valuation rule:
- Imports: use CIF when available.
- Exports: use FOB when available.
- Never add CIF and FOB together.
- Store and display the measure actually used.
- If the expected measure is unavailable, do not silently fabricate or estimate a value. Mark it unavailable until the team has documented and tested an agreed fallback.

**To validate:** Confirm actual response fields and exact query parameters for both trade directions. Do not assume `primaryValue` always means the desired measure for every query.

UN Comtrade may return total records together with customs, transport, and second-partner breakdowns. Never sum a total row with its breakdowns. Do not assume a total-row filter tested for one product/year works for every product, year, classification, and direction.

A previous sample response contained 272 rows for Türkiye-reported imports from China, HS 610910, in 2023. A candidate total row used partner2=World, customs C00, and total transport mode 0. This is only a test case, not a universal rule. Revalidate with representative queries before production.

## 5. Architecture: choose one compatible stack

A previous planning document proposed Python + Streamlit + PostgreSQL. Later planning discussed Supabase as hosted PostgreSQL and Vercel for deployment. These choices must not be mixed without checking compatibility.

**Before implementation, Tao and Mert must explicitly confirm:**
1. Frontend/application framework.
2. Where trusted server-side API code will run.
3. Database provider (Supabase is the current candidate).
4. Hosting/deployment platform compatible with the selected framework.

Regardless of stack:
- All database writes must go through trusted server-side code.
- Users must not write directly to the database.
- Never expose database service-role keys or other secrets in browser code.
- Store secrets in environment/hosting settings; ignore `.env` in Git.
- `.env.example` must contain placeholders only.
- Use safe, parameterized database queries or equivalent safe APIs.
- Apply least-privilege access policies.
- Check current free-tier quotas and data-use terms before public deployment.

## 6. Database contract — logical model

Finalize exact SQL types and constraints after inspecting the real API response and confirming the framework.

### `products`
- Internal product ID
- HS `product_code` stored as text
- Canonical English product/category name
- Optional parent category
- Classification name and version
- Source and catalogue update metadata
- Active status if needed

Do not assume the HS code alone is globally unique across all classifications/versions.

### `product_aliases`
- Alias ID
- Product foreign key
- Alias text
- Language code (`tr`, `en`, `zh`)
- Alias source
- Review status

Distinguish machine-translated aliases from human-reviewed aliases.

### `annual_trade_values`
- Product identity/code
- Trade direction
- Year
- Validated annual USD value
- Actual valuation measure (`CIF` or `FOB`)
- Source name
- Retrieval timestamp
- Reporter and partner codes
- Classification and version
- Query parameters/signature where useful

Expected uniqueness rule: product identity + trade direction + year, adding classification/version where necessary to avoid mixing incompatible codes. Confirm this against the actual data model before finalizing the database constraint.

### Optional `data_refresh_log`
- Query signature/parameters
- Start and finish timestamps
- Success/failure status
- Number of records
- Safe error summary

Never store credentials in logs.

## 7. Data flow

1. User enters a product name or HS code.
2. Server searches catalogue and aliases.
3. If ambiguous, the UI asks the user to select a category.
4. User selects trade direction and year range.
5. Server validates the range and builds the correct UN Comtrade query.
6. Server checks whether validated annual data is already cached.
7. If needed, server requests missing data.
8. Server validates country codes, flow, product code, classification, year, measure, and intended total row.
9. Server inserts or updates validated annual values.
10. Server calculates annual values and year-over-year changes.
11. UI displays chart, table, source details, and missing-data/error messages.

Different states must remain distinct: no product match, ambiguous product, no data for period, invalid query, API/source failure, and valid data.

## 8. Mert and Tao responsibilities

### Mert — data, SQL, validation, analysis
- Own the data dictionary and internal field definitions.
- Design and document tables, keys, constraints, and indexes.
- Import and validate the product catalogue and aliases.
- Test classification versions and code mappings.
- Define and test the total-row selection rules.
- Write SQL for annual values and year-over-year changes.
- Test missing years, duplicates, and update behavior.
- Confirm chart/table values match query results.
- Document methodology and limitations.

### Tao — API, UI, integration
- Implement the UN Comtrade API client and direction parameter mapping.
- Preserve the exact query parameters used.
- Handle empty responses, timeouts, API errors, rate limits, and missing fields.
- Convert source responses to the agreed internal format.
- Implement trusted server-side reads/writes to the database.
- Build search, category selection, direction and year controls.
- Connect chart/table outputs to the UI.
- Configure hosting after the framework is confirmed.

### Shared responsibilities
- Agree on field names and the data contract before integration.
- Review the source query mapping and total-row rules together.
- Test both directions, several years, missing data, duplicates, and API failures.
- Keep README/setup instructions accurate.
- Do not change schema or shared field names without notifying each other.

## 9. Required tests before calling the MVP functional

- Product code and classification version are correct for test products.
- Turkish, English, and Chinese aliases work for the aliases present in the catalogue.
- Ambiguous searches offer choices.
- Both directions use correct reporter, partner, and flow.
- Total-row filters exclude overlapping breakdowns.
- CIF/FOB selection follows the documented rule and actual available fields.
- Chart and table use the same annual values.
- Year-over-year calculations are correct.
- Missing year is not shown as zero.
- Missing prior year and zero prior value are handled as `N/A` where required.
- Invalid year range is rejected.
- Repeated queries do not create duplicates.
- Updated values replace the existing record for the same unique key.
- API failure produces a clear message.
- No secret is exposed in browser code, logs, or GitHub.
- End users cannot write directly to the database.
- Source, reporting perspective, HS code/version, and measure are visible.

## 10. Recommended implementation order

1. Validate one real UN Comtrade query for a selected product and document the exact parameters.
2. Confirm framework, server runtime, database provider, and deployment platform.
3. Freeze the shared field mapping and database contract.
4. Import a suitable product catalogue and add/test aliases.
5. Implement server-side ingestion and caching/upsert.
6. Implement SQL/analysis and validate the results manually.
7. Build the UI and connect it to the real data flow.
8. Test the required cases.
9. Review current data-use terms and hosting limits, then deploy.
10. Collect feedback and prioritize future improvements.

## 11. Out of scope for the MVP

Do not build unless the team explicitly agrees later:
- AI-first product matching
- Forecasting or machine-learning predictions
- Profitability recommendations
- Countries beyond Türkiye and China
- Multi-product charts
- CSV/Excel exports
- Search history
- Scheduled refresh jobs
- Detailed customs/transport/second-partner breakdowns
- TRY/CNY conversion
- Accounts/subscriptions without a real need

## 12. How the AI should help the team

When asked to implement something:
1. State the goal and why it matters in beginner-friendly language.
2. Identify prerequisites and unresolved assumptions.
3. Propose the smallest testable step.
4. Explain the code and important parameters clearly.
5. Add concise English comments suitable for GitHub.
6. Include a way to test the result and explain what success/failure means.
7. Do not claim a step worked unless it was actually run or verified.
8. Keep Mert's SQL/data responsibilities and Tao's API/UI responsibilities clear.
9. If a requirement conflicts with this brief, point out the conflict and ask before changing scope.
