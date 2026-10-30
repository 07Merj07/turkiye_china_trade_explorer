# Türkiye–China Trade Explorer
## Master Project Specification & Implementation Contract

**Document status:** Consolidated working specification  
**Purpose:** Single primary reference for Mert, Tao, and their AI assistants  
**Language:** English, so both teammates and coding assistants can use it  
**Scope:** MVP only, unless a section explicitly labels something as future work

> **Source-of-truth rule:** Use this document as the current consolidated specification. Earlier planning documents are background only and must not override this file. If an older document conflicts with this one, flag the conflict instead of silently choosing. Do not treat any example response or candidate query as proof that all queries work.

---

# 1. Project summary

Türkiye–China Trade Explorer is a web application for exploring official merchandise-trade statistics between Türkiye and China by product and year.

A user searches for a product using a Turkish, English, or Chinese term, or enters an HS product code. The app presents plausible official product categories from a product catalogue. The user selects the intended category, chooses one of the two supported trade directions, selects a year range, and sees annual trade values, year-over-year changes, a chart, and source/methodology notes.

The project is an evidence-based trade research tool. It is **not** an automatic profitability predictor, consumer-demand model, customs-cost calculator, or guarantee that a product will sell well.

## Main user value

Make official Türkiye–China trade data easier to find, interpret, and trace back to its source without requiring the user to understand UN Comtrade query parameters or HS classification details.

## Success in one sentence

A user can search for a supported product, choose the correct product category and trade direction, select a valid year range, and see correctly validated annual trade values with transparent source and missing-data handling.

---

# 2. MVP decisions: what is in and out

## 2.1 Included in the MVP

- Türkiye and China only; no country selector for other countries.
- Product search by:
  - HS code
  - Turkish product names, where supported by the catalogue/alias table
  - English product names
  - Chinese product names, where supported by the catalogue/alias table
- Official product catalogue kept separate from annual trade records.
- Product categories/sub-products and classification version displayed.
- Ambiguous product matches shown as options; never force a questionable match.
- Two fixed trade-direction options:
  - `TURKEY_TO_CHINA`
  - `CHINA_TO_TURKEY`
- Year-range selection from 2010 to the latest year actually available for the selected query; start year must be less than or equal to end year.
- USD values only in the main MVP interface.
- One primary annual line chart.
- A compact annual values table.
- Year-over-year (YoY) absolute USD change and percentage change, where valid.
- Exact value visible on chart hover/tap.
- Clear missing-data and API-error messages.
- Source and methodology information: source, reporter/partner perspective, year, HS code/classification, and actual valuation measure where available.
- Server-side API/database access.
- Fetch missing data on demand and cache validated results.
- Update an existing matching record rather than inserting a duplicate.
- Basic tests for direction mapping, annual totals, duplicate handling, missing years, YoY calculations, and API failures.
- English user interface.
- GitHub README with setup, data source, methodology, limitations, and usage instructions.

## 2.2 Explicitly out of scope for the MVP

Do not implement these unless the team explicitly changes this specification:

- CSV/Excel export
- Search history or user accounts
- Scheduled/background refresh jobs
- Multi-product comparison screens
- Forecasting or predictive AI
- Profitability predictions or investment recommendations
- Consumer-demand claims inferred from trade values alone
- Full customs, shipping, tax, insurance, margin, or logistics-cost calculations
- Other countries or partner selection beyond Türkiye and China
- Detailed customs/transport/second-partner breakdowns in the user interface
- Adding multiple data sources just for the sake of having more sources
- AI-first product matching that hides uncertainty
- Automatic silent fallback to another measure or classification
- Showing invented sample figures as if they were real
- Bulk downloads of raw data archives

These are exclusions to protect a deliverable MVP, not statements that the features could never be added.

---

# 3. Product search and HS classification

## 3.1 Catalogue versus trade data

Keep two concepts separate:

- **Product catalogue:** Which official product code and description represent a product, under which classification/version?
- **Trade records:** What value was reported for that product, country pair, flow, and year?

The catalogue is not itself evidence that trade occurred. A valid product code can have no usable record for a particular query/year.

## 3.2 Catalogue requirements

The catalogue should store, where available:

- Classification name, e.g. HS
- Classification version, e.g. HS 2022
- Product code
- Official description
- Parent/category relationship, if supplied or reliably derived
- Source name
- Catalogue import/update timestamp
- Validity period or year applicability, if supplied by the source

Do not assume a code is globally unique without its classification/version context. Do not assume one HS code maps consistently across all historical years.

A supplied cleaned HS2022 catalogue can be used as a starting data asset, but its columns, completeness, code formatting, hierarchy, licence/attribution, and intended year coverage must be inspected before production use. Do not treat the file name as proof that every row is correct.

## 3.3 Search behaviour

Recommended MVP matching sequence:

1. Normalize harmless differences such as extra whitespace and case where applicable.
2. Search exact product-code matches.
3. Search exact official descriptions and reviewed aliases.
4. Search approximate text matches as a fallback.
5. Show plausible categories with code, official description, and classification version.
6. If multiple plausible results exist, let the user choose.
7. If no suitable result exists, say “No match found” and suggest trying another term or HS code.

Do not indiscriminately remove Turkish characters or alter Chinese text. Do not claim that every Turkish/English/Chinese phrase will work unless tested. Machine-translated aliases should be distinguishable from human-reviewed aliases.

## 3.4 Product-match quality tests

Prepare a small, documented test set with:
- Input phrase
- Language
- Expected product code/category
- Expected outcome
- Actual outcome
- Pass/fail
- Notes about ambiguity

Include exact matches, synonyms, typos, ambiguous terms, Chinese terms, and unknown terms. Measure whether the correct category appears and whether uncertainty is handled appropriately—not merely whether the search returns something.

---

# 4. Trade directions and reporting perspective

The MVP has exactly two user-facing directions:

## `TURKEY_TO_CHINA`

Meaning: Türkiye-reported exports to China.

Candidate query mapping:
- Reporter: Türkiye
- Partner: China
- Flow: Export

## `CHINA_TO_TURKEY`

Meaning: China-reported exports to Türkiye.

Candidate query mapping:
- Reporter: China
- Partner: Türkiye
- Flow: Export

These labels describe the direction of reported exports from the reporting country's perspective. The actual UN Comtrade API codes and parameter names must be confirmed against current documentation and a real response before implementation is finalized.

Do not casually substitute “Türkiye-reported imports from China” for “China-reported exports to Türkiye.” Those are mirror perspectives and can differ because of valuation, timing, classification, coverage, and reporting practices.

**Never add the two reporting perspectives together.** The MVP does not need to compare or combine mirror records. Show which country reported the data.

The team must test each direction independently with a known query. One successful example is not enough to prove every product/year query is correct.

---

# 5. UN Comtrade API integration

## 5.1 General rules

UN Comtrade is the intended primary source for merchandise trade statistics. Verify current API documentation, access limits, and terms during implementation. Do not hard-code unverified quota assumptions.

The API client must:
- Build query parameters explicitly and consistently.
- Keep reporter, partner, flow, product code, classification, period, and valuation/measure metadata traceable.
- Handle timeouts, HTTP/API errors, malformed responses, and empty results.
- Avoid exposing API keys or database credentials.
- Convert source responses into a documented internal data contract.
- Preserve enough query metadata to reproduce or explain the result.
- Avoid unnecessary repeat requests by using a defined cache policy.

No automatic retry system is required for the MVP unless the team later agrees it is needed. An API error must produce a clear user-facing message rather than a fake zero value.

## 5.2 Example JSON is illustrative, not universal

The file `response_1792842463800.json` is an example response. It has been observed to contain many records and fields, including breakdown dimensions. It is useful for learning the response structure, but it does **not** prove that:
- Every query returns the same fields or number of rows.
- Every query has a single obvious total row.
- A candidate filter is valid for every product/year.
- The same result exists for both trade directions.
- A query that works for one year will work for all years.

Inspect actual responses and current API documentation. Record the exact request parameters for each validation query.

## 5.3 Total rows and breakdowns: double-counting risk

UN Comtrade responses may contain a total record and additional records broken down by customs, mode of transport, second partner, or other dimensions. Do not sum totals and their component breakdowns together.

For MVP annual totals:
- Decide which record level represents the intended aggregate.
- Inspect available dimensions and total indicators in the actual response.
- Select one consistent, validated aggregation level.
- Reject or flag ambiguous responses rather than summing blindly.
- Keep detailed breakdowns out of the MVP UI.

A candidate filter observed in one sample is not a universal rule. Validate total-row selection with multiple products, years, and both directions.

## 5.4 Validation before relying on results

For each test query, retain:
- Exact query parameters
- Retrieval timestamp
- Response status
- Relevant source fields
- Selected record(s) and why they were selected
- Excluded breakdowns/records and why
- Expected versus observed result, if a reliable comparison exists
- Known limitations

Do not publish real-looking trade values until a real API query has been validated.

---

# 6. Valuation measures: CIF and FOB

The MVP displays USD values only, but the actual valuation measure must be preserved and disclosed.

- Imports are commonly reported on a CIF basis where applicable.
- Exports are commonly reported on an FOB basis where applicable.
- Do not add CIF and FOB values together.
- Do not silently replace an unavailable measure with another measure.
- Do not label a value “CIF” or “FOB” unless the source metadata supports that label.
- If the valuation measure cannot be determined, mark it as unknown/unavailable and decide whether the result is safe to display; do not fabricate a measure.

The exact source fields and any exceptions must be checked in the real API response and official documentation. Store the actual measure or a clearly defined unknown state.

---

# 7. Year selection, missing data, and YoY logic

## 7.1 Year range

- The user can select a start year and end year.
- Earliest selectable year: 2010, subject to the query and source availability.
- Latest selectable year: the latest year actually available for the selected product/direction/query, not simply the current calendar year.
- Start year must be less than or equal to end year.
- Do not promise data for every year in the range.

## 7.2 Missing years are not zero

If a year has no usable record, show `No data` for that year and preserve the gap in the chart. Do not automatically replace missing data with numeric zero.

“No record returned” does not prove that no trade occurred. A clear no-data message should be shown when the selected period has no usable records:

`No data available for this period.`

If the API fails, show an error message distinct from the no-data message. Do not treat a failed request as an empty result.

## 7.3 YoY calculations

For a current year with value `current` and the immediately preceding calendar year's value `previous`:

- Absolute change = `current - previous`
- Percentage change = `(current - previous) / previous * 100`, only when `previous > 0`

Rules:
- If the immediately previous calendar year is missing, YoY is `N/A`.
- If the previous value is zero, percentage change is `N/A` to avoid division by zero.
- Do not compare against the previous available year if it skips a calendar year, unless the interface explicitly labels that different comparison. The MVP should use the immediately previous calendar year.
- Do not imply a zero value where the source has missing data.
- The first year in a selected range may need the prior calendar year's data to calculate YoY. If it is not available in the database, retrieve/validate it if feasible; otherwise show `N/A`.

Test positive, zero, missing, negative-change, and first-year cases. Trade values should be validated as source data; do not silently discard unusual values without a documented rule.

---

# 8. Main screen and results behaviour

## 8.1 Required results

Display:
- Selected product name
- HS code and classification/version
- Trade direction
- Reporting country and partner
- Selected year range
- Annual USD values
- YoY absolute change in USD
- YoY percentage change where valid
- One primary annual line chart
- Compact yearly values table
- Exact chart-point value on hover/tap
- Source and retrieval information
- Actual valuation measure if known
- Data notes/limitations when relevant

## 8.2 Language and interaction

- User interface language: English for the MVP.
- Product search may accept Turkish, English, and Chinese inputs where catalogue aliases support them.
- If the selected product is ambiguous, show options and wait for the user to choose.
- If there are no matching products, explain that no match was found.
- If the period has no usable trade records, show the specified no-data message.
- If the API fails, distinguish the error from no data.
- Do not show fabricated sample figures as real results.
- Do not add comparison charts, extra product breakdowns, export controls, or search history to the MVP.

---

# 9. Database and data contract

The database design must be finalized only after inspecting actual API fields and agreeing on the internal data contract. The field names below are conceptual recommendations, not a claim that a production schema already exists.

## 9.1 Suggested logical entities

### `products`
Stores official product classifications:
- Internal product ID
- Classification name
- Classification version
- Product code
- Official description
- Parent/category reference if applicable
- Source name
- Catalogue update/import timestamp
- Validity metadata if available

### `product_aliases`
Stores searchable alternative names:
- Alias ID
- Product ID
- Language code (`tr`, `en`, `zh`, as appropriate)
- Alias text
- Alias source (official, human-reviewed, machine-translated, etc.)
- Review status

### `trade_records`
Stores validated annual trade observations:
- Internal record ID
- Reporter code/name
- Partner code/name
- Product ID or code plus classification/version
- Year/period
- Flow code/description
- Trade value
- Currency (USD for the MVP presentation; retain source metadata as appropriate)
- Valuation measure (CIF, FOB, or explicitly unknown)
- Quantity and quantity unit only if available and reliably defined
- Source name
- Retrieval timestamp
- Relevant source record identifiers/dimensions needed to identify the selected aggregate
- Query metadata or a reference to stored query metadata

### `data_refresh_log` or equivalent metadata
Records retrieval/validation attempts, outcomes, timestamps, and errors where useful.

The team may adjust table names and split metadata into separate tables, but must document the final schema and explain why it is appropriate.

## 9.2 Keys and duplicate prevention

Do not define uniqueness based only on year or product code if multiple reporters, partners, flows, classifications, or measures can exist.

The natural uniqueness key must reflect the exact selected aggregate. Candidate dimensions include:
- Product identity and classification/version
- Trade direction or reporter + partner + flow
- Year/period
- Measure/valuation where it affects record identity
- Any source dimension required to distinguish the chosen aggregate

Confirm the final key after inspecting the API fields. Enforce it with a database constraint where possible. When the same validated record is fetched again, update the existing record or its retrieval metadata rather than creating a duplicate.

## 9.3 Write access and SQL safety

- The browser/user must never write directly to the database.
- Server-side application code performs database operations.
- Use parameterized SQL queries.
- Keep credentials in environment variables/secrets, not source code.
- Use `.gitignore` for `.env`.
- `.env.example` contains placeholders only.
- Restrict database permissions to the minimum needed.
- Error messages must not reveal secrets.
- Define a basic backup/recovery approach before deployment.

## 9.4 Cache policy

The MVP can fetch missing data on demand and cache validated values. The team must agree on how to determine whether a cached record is reusable and how to record retrieval time. No scheduled refresh is required for the MVP.

Do not cache an API failure as though it were a valid empty result. Store enough metadata to distinguish successful no-data responses from failed requests.

---

# 10. Technical stack and architecture decisions

## 10.1 Still to be confirmed

The older planning guide recommended Python + Streamlit + PostgreSQL. Later planning considered other deployment/database options. The stack must not be treated as fully finalized until the team explicitly confirms it.

Decide these together as a compatible set:
1. Web framework/UI
2. Server-side runtime
3. PostgreSQL hosting/provider
4. Deployment/hosting platform
5. Environment-variable/secrets setup

Do not mix incompatible assumptions—for example, do not assume a frontend-only hosting service can directly run a Python/Streamlit app. Verify the current capabilities, free-tier limitations, persistent storage, and cost implications before choosing.

## 10.2 Logical architecture regardless of final stack

- UI gathers product, direction, and year-range selections.
- Product-search module matches input against the product catalogue and aliases.
- Server-side API client requests source data.
- Validation/normalization layer checks response records and selects the correct aggregate.
- Database stores catalogue, aliases, validated trade records, and metadata.
- Analysis layer calculates annual values and YoY changes.
- Chart/table layer displays only validated results and explanatory metadata.

Keep API/data access, database operations, matching, analysis, and UI code separated enough to test independently.

## 10.3 Possible code modules

A starting layout—not a rigid requirement:

```text
project/
  app/ or app.py
  src/
    api_client.py
    product_matching.py
    data_validation.py
    database.py
    analysis.py
  sql/
    schema.sql
    analysis_queries.sql
  tests/
    test_product_matching.py
    test_data_validation.py
    test_database.py
    test_analysis.py
    test_direction_mapping.py
  docs/
    data_dictionary.md
    methodology.md
    decisions.md
  README.md
  .gitignore
  .env.example
```

Adapt to the chosen framework. Do not create modules solely to match this example if a simpler structure is more suitable.

---

# 11. Division of responsibilities: Mert and Tao

## Mert — data, SQL, and analysis owner

Primary responsibilities:
- Inspect and document catalogue fields and classification versions.
- Import/validate product catalogue and build the alias data model.
- Design SQL schema, types, constraints, relationships, and indexes.
- Define the internal data contract with Tao.
- Define record identity and duplicate-prevention rules.
- Define total-row selection and double-counting safeguards.
- Validate data quality and source metadata.
- Implement or validate annual totals and YoY logic.
- Build analysis/database tests.
- Write the data dictionary and methodology sections of the README.

Learning goal: understand why each table, field, key, constraint, query, and calculation exists—not merely copy code.

## Tao — API, UI, and integration owner

Primary responsibilities:
- Inspect current UN Comtrade API documentation.
- Implement the API client and exact query-parameter mapping.
- Save exact query parameters for validation examples.
- Handle errors, timeouts, empty responses, and malformed responses.
- Convert API responses into the shared internal data contract.
- Build the English UI, product-selection flow, year controls, table, and chart.
- Integrate the UI with the server-side database/analysis functions.
- Add API/UI integration tests.
- Support deployment after the stack is agreed.

## Shared responsibilities

- Confirm MVP scope and stack.
- Agree on the data contract and field names before final integration.
- Test both trade directions.
- Review product-match ambiguity and no-data behaviour.
- Review record selection and CIF/FOB handling.
- Review end-to-end results before expanding to more products.
- Keep Git branches/commits understandable and review changes before merging.
- Ensure both people understand the basic flow of the other person's work.

No one should silently change a shared field name, key, direction mapping, or calculation rule. Discuss it and update the specification/data contract.

---

# 12. Testing and acceptance checklist

The MVP is not complete just because the page loads. Record the outcome of these tests.

## Product search
- [ ] A supported HS code returns the expected product.
- [ ] An exact supported product name returns the expected category.
- [ ] A Turkish alias works if present in the alias table.
- [ ] An English alias works if present.
- [ ] A Chinese alias works if present.
- [ ] Ambiguous input presents options rather than silently choosing.
- [ ] Unknown input produces a clear no-match message.
- [ ] Classification version is visible.

## Trade direction and API
- [ ] `TURKEY_TO_CHINA` maps to Türkiye reporter, China partner, export flow.
- [ ] `CHINA_TO_TURKEY` maps to China reporter, Türkiye partner, export flow.
- [ ] Each direction has been tested independently against a real response.
- [ ] Exact query parameters are recorded.
- [ ] Empty result and API failure are handled differently.
- [ ] Malformed/unexpected response is not silently treated as valid data.
- [ ] Total records are not added to their breakdown records.
- [ ] CIF/FOB is not guessed or silently substituted.

## Database
- [ ] Product codes preserve leading zeros if relevant.
- [ ] Classification/version is represented.
- [ ] Relationships between products, aliases, and trade records are valid.
- [ ] Re-fetching the same aggregate does not create a duplicate.
- [ ] Database operations use parameterized queries.
- [ ] No secrets are committed to GitHub.

## Analysis and UI
- [ ] Annual values match independently checked calculations.
- [ ] Missing year is shown as missing, not zero.
- [ ] Chart has a gap for missing data.
- [ ] Absolute YoY change is correct.
- [ ] YoY percentage is `N/A` when previous year is missing or zero.
- [ ] The comparison uses the immediately previous calendar year.
- [ ] Chart hover/tap shows the exact value.
- [ ] Selected product, HS code/version, direction, year range, source, and measure are identifiable.
- [ ] No-data message is shown when no usable records exist for the selected period.
- [ ] API error message is clear and does not expose credentials.

## Deployment and documentation
- [ ] Stack is explicitly agreed by both teammates.
- [ ] Public deployment works with secrets configured server-side.
- [ ] `.env` is ignored; `.env.example` has placeholders only.
- [ ] README includes setup, source, methodology, limitations, and usage.
- [ ] Known limitations and test outcomes are documented.

---

# 13. Data source, methodology, and honest interpretation

The app should explain:
- Data source: UN Comtrade, with relevant source link.
- Reporting country and partner.
- Trade direction and flow.
- HS code and classification version.
- Year/period.
- Currency and valuation measure where known.
- Retrieval timestamp or source-update note.
- What the annual total represents and which records were selected.
- Missing data and comparability limitations.

Interpretation cautions:
- Missing record is not the same as zero trade.
- Türkiye's reported import values and China's reported export values may differ.
- A rise in nominal USD value does not necessarily mean more physical units were traded.
- Trade values alone do not prove consumer demand or profitability.
- Product-code classification can change over time.
- Source data may be revised.
- Quantity must not be interpreted without its unit and definition.

Do not overclaim what the tool can conclude.

---

# 14. Development sequence

Follow this order unless a concrete blocker requires a change.

## Phase 1 — Confirm the contract
- Read this document.
- List unresolved decisions.
- Agree on the stack.
- Agree on the first test product and exact test queries.
- Agree on the shared data contract.

**Why:** Building UI and database tables before validating the source response can force expensive redesign.

## Phase 2 — Validate real API responses
- Tao builds a small request for one product and one year for each direction.
- Record the exact parameters and response.
- Mert inspects the candidate aggregate and the risk of double counting.
- Confirm the valuation metadata and fields actually available.

**Why:** The app should be based on real response behaviour, not assumptions from a sample file.

## Phase 3 — Product catalogue and database
- Inspect the provided catalogue file.
- Validate codes, descriptions, hierarchy, version, and source.
- Design tables and constraints.
- Import a small sample, then validate the full catalogue.
- Agree on aliases and review status.

**Why:** Product search and trade records need stable, version-aware identifiers.

## Phase 4 — Shared data contract and persistence
- Define exact field names/types.
- Normalize API records into the agreed format.
- Implement duplicate prevention/upsert behaviour.
- Save source/query/retrieval metadata.
- Test successful, empty, and failed requests.

**Why:** Tao's API module and Mert's database must agree on what each field means.

## Phase 5 — Analysis and tests
- Implement annual totals using only validated aggregate records.
- Implement missing-year handling and YoY calculations.
- Compare calculations with independently checked examples.
- Add unit tests.

**Why:** A polished chart is not useful if the underlying totals are wrong.

## Phase 6 — UI integration
- Build search and category selection.
- Build direction/year controls.
- Display annual chart and compact table.
- Add source and limitation notes.
- Add no-match, no-data, and API-error states.

**Why:** The interface should reveal the validated data, not conceal uncertainty.

## Phase 7 — End-to-end review and deployment
- Run the acceptance checklist.
- Resolve failed tests.
- Agree on and configure deployment.
- Check free-tier/persistence/cost limitations.
- Publish setup and methodology documentation.

**Why:** Deployment is the final delivery step, not a substitute for validation.

---

# 15. Known observations versus unverified assumptions

The team has previously observed in an example JSON response that it contained 272 records and 47 fields. A narrow 2023 test query was reported to return one candidate record matching a candidate total, and a similar 2025 query was also observed to return one record. The sample included multiple breakdown dimensions.

These are **initial observations only**. They are not proof that:
- The chosen filter is correct for every query.
- The data is fully validated.
- The same field names/values appear in every response.
- Every year/product has a usable record.
- Both reporting perspectives match.
- The valuation measure is always available.

Treat these observations as test leads. Reproduce and document them before relying on them in the application or README.

---

# 16. Unresolved decisions register

The AI assistant must identify these as open decisions unless the team has explicitly recorded a later answer.

1. **Final stack:** Streamlit/Python/PostgreSQL versus alternatives; choose UI, runtime, database host, and deployment together.
2. **Database provider and hosting:** Must be compatible with the selected framework and budget.
3. **Exact source query mapping:** Confirm current API parameter names and codes for both directions.
4. **Aggregate-row rule:** Identify the correct total/aggregate selection based on real responses and dimensions.
5. **Valuation metadata:** Confirm where/how CIF/FOB or equivalent valuation is represented, and define behaviour if unavailable.
6. **Classification coverage:** Confirm which catalogue version is used and how historical years with different classifications are handled.
7. **Catalogue validation:** Inspect the supplied cleaned workbook before treating it as production-ready.
8. **Cache freshness:** Define when cached records may be reused and how source revisions are handled.
9. **Latest available year:** Define how the app determines availability for each query without assuming the current year has data.
10. **Source-use terms:** Recheck current UN Comtrade data/API terms before public deployment.

Do not hide open decisions inside code defaults. Recommend an option, explain the trade-off, and ask the team to confirm when the choice affects architecture or data correctness.

---

# 17. Instructions for AI assistants working on this project

1. Treat this file as the primary consolidated specification.
2. Do not blindly follow older project documents if they conflict with this one.
3. Before coding, summarize the requirements and list unresolved decisions.
4. Work in small, testable steps; do not generate the whole app in one unreviewable block.
5. Explain the purpose of each step and why it is needed.
6. Clearly distinguish:
   - confirmed decision,
   - observed result,
   - hypothesis,
   - open question.
7. Never invent API parameters, field names, trade values, or successful test results.
8. Inspect actual files/responses before claiming their structure.
9. Do not treat one sample JSON response as universal.
10. When a decision changes the database schema, direction mapping, record selection, or calculations, stop and flag it for team agreement.
11. Preserve uncertainty and missing-data distinctions.
12. Give Mert beginner-friendly explanations of SQL/data choices, including what a query does and why.
13. Give Tao concrete API/UI implementation steps and integration requirements.
14. Do not add out-of-scope features without explicit approval.
15. At the end of each implementation step, state what changed, why, how to test it, and what remains unresolved.

---

# 18. Official references to check during implementation

Use current official documentation rather than relying only on this planning file:
- UN Comtrade portal: https://comtradeplus.un.org/
- UN Comtrade documentation/help: https://uncomtrade.org/docs/
- World Customs Organization HS overview: https://www.wcoomd.org/en/topics/nomenclature/overview/what-is-the-harmonized-system.aspx
- PostgreSQL documentation: https://www.postgresql.org/docs/
- Streamlit documentation, if Streamlit is selected: https://docs.streamlit.io/
- GitHub documentation: https://docs.github.com/

API parameters, source terms, free-tier limits, and hosting features can change. Verify them at the point of implementation.

---

# 19. Final operating rule

**Build the smallest reliable end-to-end path first:** one supported product, one tested query for each direction, validated aggregate records, correct SQL persistence, correct annual/YoY calculations, and a simple chart/table with source notes.

Only expand the catalogue or interface after that path has been tested. Correctness, traceability, and clear handling of uncertainty are more important than adding many features.
