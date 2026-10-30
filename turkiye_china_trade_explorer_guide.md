# Türkiye–China Trade Explorer
## Product Research, Data Analysis, and Web Application — Project Specification and Implementation Guide

**Document type:** Project specification, implementation plan, and division of responsibilities  
**Project name:** Türkiye–China Trade Explorer  
**Version:** 1.0 — planning draft  
**Goal:** Build a feasible, testable first version that a two-person team can understand and implement

> **Important note:** This document describes a plan for the application; it is not a completed application and has not yet been validated against real data. Example product names and screens are illustrative. No actual trade values should be shown until a data query has been run.

---

## 1. Project overview

Türkiye–China Trade Explorer is a web application that allows users to enter a product name in everyday language, research official international trade data for that product category between Türkiye and China, and explore the results using clear charts.

For example, a user types “solar panel.” The system attempts to match the phrase with suitable categories in an official product classification. If several categories are plausible, the user is shown options. After selecting the correct category, the user chooses country, trade flow, and period filters. The application retrieves the relevant data through UN Comtrade, validates the records, stores them in the database or reuses cached results, and displays annual trade values, changes, and data limitations.

**The project's scope is limited to Türkiye and China.** Users cannot select other countries. In its first version, the application does not make definitive claims about profitability, consumer demand, or future sales based on trade data alone. Its purpose is to make preliminary product-level trade research easier and more understandable.

### The core promise

“Enter a product name, find the appropriate official product category, and explore the relevant trade records and year-by-year changes between Türkiye and China in one place.”

### Goals for the first version

- Allow users to enter product names as free text.
- Support searches in Turkish, English, and, as far as practical, Chinese.
- Use a catalog of official product codes and descriptions.
- Offer choices when a match is ambiguous.
- Query trade only between Türkiye and China.
- Provide import/export, reporting-country, and period filters.
- Show UN Comtrade data with its source and coverage clearly identified.
- Produce basic analyses such as annual totals and year-over-year change.
- Include tests for the database, API integration, and analysis logic.
- Aim to publish the application so it can be accessed online.

---

## 2. What problem are we solving?

International trade data is available, but researching it may not be easy for beginners. A user may need to find a product's official code, choose the right classification, specify the correct country and trade flow, inspect records across years, and interpret the results.

Trade Explorer aims to bring this process together in one workflow:

1. The user searches using their own words.
2. The system finds possible official product categories.
3. The user chooses the appropriate category.
4. The user selects which direction of Türkiye–China trade and which period to examine.
5. The system retrieves available data and runs basic quality checks.
6. The user sees charts, annual values, changes, and data notes.

### What the project does not solve

The first version does not guarantee that it can:

- Determine whether a product will be profitable in Türkiye.
- Predict future sales or consumer demand with certainty.
- Calculate all customs, shipping, insurance, tax, competition, and sales costs.
- Recognize every phrase typed by the user without error.
- Find data for every product and every year.
- Present official trade statistics as real-time market prices.

An increase in trade value alone does not prove that consumer demand or profitability has increased.

---

## 3. Target users and use cases

### 3.1 Small business owner or entrepreneur

A business owner is considering importing solar panels from China. Before placing an order, they want to investigate how much Türkiye imported from China in this product group in different years and how the reported trade value changed.

The application makes the initial research step easier. The user must still conduct additional research into suppliers, costs, and profitability.

### 3.2 Import/export analyst

An analyst is asked to prepare a preliminary report on a particular product group in Türkiye–China trade. They select the product category and period filter, review the annual table and chart, and use them to prepare an initial assessment.

### 3.3 Student or researcher

A student researches Türkiye–China trade in a particular product group. They check the source, period, and classification notes before citing the findings in a report.

### Initial user group

Rather than targeting every possible user immediately, it makes sense to test the prototype with students, analysts, and small businesses that need quick preliminary research on Türkiye–China trade. User interviews can help identify which features are genuinely useful.

---

## 4. How will a user use the application?

### Screen 1 — Home page and product search

The user arrives at a simple home page. Beneath a prompt such as “Which product would you like to research?”, they enter a product name in a search box.

Examples:
- solar panel
- olive oil
- textile product
- the Turkish phrase for a solar panel
- a Chinese product name the user knows

These are examples of search terms; they do not mean the system will match all of them perfectly from day one.

### Screen 2 — Possible product categories

The system searches for the entered phrase in the product catalog. If it finds suitable matches, it displays:

- Official product description
- Product code
- Classification version to which the code belongs
- Turkish and Chinese descriptions, where available
- How certain the match is, or why more than one option is being offered

For example, searching for “solar panel” may require distinguishing photovoltaic cells assembled into modules/panels from cells that have not yet been assembled into modules. Under HS 2022, these are different categories. Such codes must always be used together with the relevant classification version.

The user selects the correct product. The system must not present an uncertain match as if it were definitely correct.

### Screen 3 — Trade filters

The user selects the following options:

- **Reporting country:** Türkiye or China
- **Trading partner:** The other country; only the Türkiye–China pair is allowed
- **Trade flow:** Import or export
- **Period:** Select from available and verified years
- **Product category:** The official category selected on the previous screen

Example:
- Reporting country: Türkiye
- Trading partner: China
- Trade flow: Import
- Period: 2020–2025

This illustrates a possible user selection; it does not claim that data for the selected product exists in every one of those years.

### Screen 4 — Results

When suitable data is available, the results screen displays:

1. Selected product name and official code
2. Reporting country, trading partner, and trade flow
3. Selected period
4. Reported trade value by year
5. Absolute and percentage change from the previous year, when calculable
6. A relevant chart
7. Data source and last checked/retrieved time
8. Warnings about missing periods, classification, or comparability
9. A short explanation of what the results do and do not mean

Do not display sample numbers on the screen before querying real data. During the design phase, chart placeholders may be used, but they must be clearly labelled as examples.

### Screen 5 — When no data is found

The system must not behave as though no available record means trade was zero. It should display a message such as:

“No usable records were found for this query for the selected product, country, trade flow, and period. This alone does not prove that no trade took place. You can check the product category, classification version, or period.”

### Screen 6 — Source and methodology

Users should be able to see where the data came from, which country reported it, which classification version applies to the product code, and which calculations were performed. This transparency is a core feature for the application's credibility.

---

## 5. What is the product catalog, and where will it come from?

Think of the product catalog as a dictionary. A normal dictionary stores words and their meanings; our catalog stores the product codes used in international trade, their official descriptions, and the relevant classification version.

### Will we write the catalog by hand?

No. We will not enter thousands of products one by one. We will obtain a suitable official product-classification reference table and bulk-import it into the database. UN Comtrade reference tables and product-classification information are starting points. The exact file and version must be verified during development.

### The product catalog and trade data are not the same thing

The **product catalog** answers: “What is the official name and code for this product?”

The **trade data** answers: “What trade value was reported for this product in the records between Türkiye and China for the selected year and trade flow?”

A product catalog obtained once and trade records collected over multiple years serve different purposes and are stored separately. Product catalogs may need updates; trade records may also need to be checked again when the source updates its data.

### Which classification will we use?

The initial design can use the Harmonized System (HS). However, the classification versions for the relevant years must be checked before applying one code to all years. Some product codes change between versions, and national classifications may be more detailed than the international six-digit level.

At a minimum, the database should store:
- Classification name and version
- Product code
- Official product description
- Information on the version or period for which the code is valid, where available
- Source name and catalog update date

### Searching in Turkish, English, and Chinese

Official catalog descriptions may not use exactly the same wording as people use in everyday speech. Therefore, we will build a search layer:

1. Import official descriptions from the catalog.
2. Create Turkish and Chinese equivalents using machine translation or language-support tools.
3. Add common alternative names and synonyms.
4. Evaluate approximate text matching or language-model-based similarity search when needed.
5. Ask the user to choose when several matches are plausible.
6. When no match is found, suggest alternative wording instead of forcing an incorrect code.

The first version should not aim to translate every product perfectly into every language. The priority is to make catalog search work and test its accuracy for common products.

---

## 6. Data source and data-use approach

### Main source: UN Comtrade

UN Comtrade will be used to access international merchandise trade statistics reported by countries. The application will query only the relevant records between Türkiye and China.

Queries generally depend on:
- Reporting country
- Trading partner
- Product code and classification
- Import or export
- Year or period
- Trade value and, where available, quantity/unit

The exact API parameter names and returned fields must be checked against the official documentation during the actual integration.

### Free access and quotas

UN Comtrade's free-access conditions and API limits may vary by plan and over time. During development, check the current official quota. Do not hard-code limits that have not been verified or assume that a limit will remain permanent.

The application should use caching to reduce unnecessary repeat requests. When a user repeats the same query, the application may reuse the cached result according to its freshness policy or check the source again.

### Data licensing and redistribution

A public analysis application and bulk redistribution of raw data are not the same type of use. Before publishing, review UN Comtrade's current data-use policy and applicable licence terms.

The first version should:
- Clearly identify the source and data coverage.
- Avoid offering a large archive of raw data as an application download feature.
- Focus the core functionality on filtering, analysis, and visualization.
- Reassess the conditions if plans emerge to redistribute raw data or offer a paid service.
- Avoid methods that conflict with the source's terms of use.

This document is not legal advice. If the application's actual distribution model changes, review the current official terms again.

### Alternative data source

World Bank data is not required for the first version. It may be considered later if additional context, such as population or macroeconomic indicators, would genuinely be useful. Do not add it merely to have a second source.

---

## 7. Data accuracy and limitations

Using an official source does not mean that complete records will exist for every product and year. Reporting schedules, product classifications, data updates, and reporting methods can differ between countries.

### Core rules

1. **Missing data is not zero.** The absence of a record does not necessarily prove that no trade took place.
2. **The two countries' reports do not have to match.** The value reported by Türkiye as imports may differ from the value reported by China as exports.
3. **Classification version matters.** A product code may change over time.
4. **Value and quantity are different concepts.** Trade value may rise while quantity stays the same or falls.
5. **Nominal values can reflect price effects.** An increase in value does not automatically mean more units were traded or demand increased.
6. **Data can be updated.** Running the same query later may produce different results because the source has updated its records.
7. **Check units.** If a quantity field is available, its unit and definition should be stored.
8. **Show the source.** Each result should explain where it came from and which query conditions were applied.

### How will imports and exports be described?

“Imports reported by Türkiye” and “exports reported by China” represent different reporting perspectives. The application should state clearly which perspective is shown and should not combine these two values into a single value without explanation.

### How will year-over-year change be calculated?

When the previous year's value is greater than zero, percentage change can be calculated as:

`(Current year's value - Previous year's value) / Previous year's value × 100`

If the previous year's data is missing or zero, percentage change should not be calculated directly; an appropriate explanation should be displayed. The system must not produce a misleading percentage in these cases.

---

## 8. Technical architecture: How will the components work together?

Recommended architecture for the first version:

- **Python:** API requests, data flow, and analytical logic
- **SQL:** Data storage, search, filtering, and aggregation queries
- **PostgreSQL:** Persistent database for the online application
- **Pandas:** Processing tabular data and running analyses when appropriate
- **Plotly:** Interactive charts
- **Streamlit:** The web interface users see
- **UN Comtrade API:** Source of international trade data
- **GitHub:** Version control and team collaboration
- **Streamlit Community Cloud or a suitable Python hosting service:** Publishing the application online

These technologies are recommendations for the first version. Before deployment, check the current terms, quotas, and persistence features of free plans.

### Data flow

1. The user enters a product name.
2. The search module looks for matches in the product catalog.
3. The user selects a category.
4. The user selects Türkiye/China as the reporting country, along with trade flow and period.
5. The application uses a valid cache if one exists; otherwise, it makes an API request.
6. The API response is validated and converted to a common internal format.
7. Data is inserted into or updated in the SQL database.
8. SQL/Python analyses calculate annual totals and changes.
9. The interface displays the results together with source and limitation notes.

### Important architectural principle

Users should not connect directly to the database. The user interface sends requests to the server-side Python application. Python runs the required queries and returns only the results needed for display.

API keys and database passwords must not be placed in the browser or in a public GitHub repository.

---

## 9. Database design

The following tables provide a suitable starting point for the first version. Final field definitions should be confirmed after inspecting the real API response.

### 9.1 `products`

Official product catalog records.

Recommended fields:
- `id`: Unique internal application identifier
- `classification`: Classification name
- `classification_version`: Classification version
- `product_code`: Official product code
- `official_description`: Official description
- `source_name`: Source
- `catalog_updated_at`: Last time the catalog was checked

Because the same code may appear in different classification versions, it may not be correct to treat `product_code` alone as unique in every case.

### 9.2 `product_aliases`

Alternative product names.

Recommended fields:
- `id`
- `product_id`: Relationship to the `products` table
- `language_code`: Language label such as `tr`, `en`, or `zh`
- `alias_text`: Alternative name
- `alias_source`: Source of the name or how it was generated
- `review_status`: Whether it has been reviewed

It is useful to distinguish names produced by automatic translation from names verified by a person.

### 9.3 `trade_records`

Trade records.

Recommended fields:
- `id`
- `reporter_code`
- `partner_code`
- `product_id`
- `period`
- `flow_code`
- `trade_value`
- `quantity`, if available
- `quantity_unit`, if available
- `source_name`
- `retrieved_at`
- Record or classification identifiers, if provided by the source

A suitable uniqueness rule should be designed around the actual API fields to prevent duplicate records. That rule should be based on the meaning of the records and the source fields after inspection, not on guesswork.

### 9.4 `data_refresh_log`

Data refresh history.

Recommended fields:
- `id`
- `query_signature`: Summary of the query parameters
- `started_at`
- `finished_at`
- `status`
- `records_received`
- `error_message`, if any

This table makes it easier to understand API errors and the time of the last refresh.

### 9.5 Caching approach

The same query should not have to run again for every user. Parameters such as product, country, trade flow, and period can form a query identifier. A freshness policy should define how long a result is considered usable.

Caching does not eliminate the possibility that the source has published new data. Therefore, the last retrieval time should be stored and data should be refreshed when necessary.

---

## 10. Product search and matching logic

The product search system is the most important part of the free-text feature.

### Stage 1 — Normalization

Standardize unnecessary spaces, uppercase/lowercase differences, and some punctuation differences in the user's input. Do not indiscriminately remove Turkish characters or Chinese text.

### Stage 2 — Exact match

Search the user's phrase among official descriptions and verified alternative names.

### Stage 3 — Approximate match

If there is no exact match, approximate text matching can be used to handle spelling mistakes or similar phrases.

### Stage 4 — Multilingual search

Search alternative names in Turkish, English, and Chinese. An open-source model for multilingual text similarity may be added later if needed. It is not essential for the first version to work.

### Stage 5 — Offer options to the user

If several categories match, the system displays them with their descriptions. The user makes the selection.

### Stage 6 — When no match is found

The system should:
- Display a “No match found” message.
- Suggest a broader term or alternative spelling.
- Avoid forcing the user to choose the wrong product code.
- If appropriate, provide a process for saving a new alternative name for later catalog review.

### How will we test matching quality?

Prepare a small test list. For each test, record the user input, expected category, and whether the result is correct. Test Turkish, English, Chinese, alternative spellings, typos, and ambiguous product names separately.

Success is not measured only by whether “the search returned a result.” We must also check whether the first result is correct, whether the correct category appears among the options, and whether the system handled uncertainty appropriately.

---
## 11. SQL and data analysis: Your learning area

SQL is not being added to this project merely as a skill to list on a CV. It will do real work in storing, searching, and analyzing the data.

### SQL topics you will learn

1. `CREATE TABLE`: Creating tables
2. Data types: Defining text, numbers, dates, and similar fields correctly
3. Primary keys and foreign keys: Relationships between tables
4. `SELECT` and `WHERE`: Selecting relevant records
5. `ORDER BY`: Sorting results
6. `GROUP BY`, `SUM`, `COUNT`, `AVG`: Grouping and summarizing
7. `JOIN`: Combining product and trade tables
8. `UNIQUE`, `NOT NULL`, and other constraints: Data integrity
9. Indexes: Speeding up relevant queries
10. Window functions such as `LAG`: Comparing with the previous year

### Example SQL logic

We may want to aggregate Türkiye's reported imports from China for a selected product by year. The query filters for Türkiye as the reporting country, China as the partner, the selected product, and the import flow; it then sums trade values by year.

The actual SQL field names and codes should be written after the database schema and API response have been verified. This document does not pretend that the production schema already exists.

### The difference between Python and SQL

- **SQL:** Stores, filters, joins, and aggregates data in the database.
- **Python:** Manages API requests, validates data, runs the analytical workflow, and communicates with the SQL database.
- **Pandas:** Processes tabular data.
- **Plotly:** Turns results into charts.
- **Streamlit:** Displays charts and filters to the user.

### Your responsibilities

Your primary ownership will include:
- Data model for the product catalog
- Alternative product names
- SQL database design
- Record validation and duplicate checks
- Annual total and change analyses
- Testing analytical results
- Data dictionary and methodology documentation

---

## 12. Division of responsibilities for a two-person team

Each work package should have a clear owner, but integration points must be tested together.

| Work package | You: SQL and data | Teammate: API and interface |
|---|---|---|
| Scope and user flow | Decide together | Decide together |
| Product classification and codes | Primary owner | Support when needed |
| Importing the product catalog into the database | Primary owner | — |
| Turkish/Chinese alternative names | Primary owner; assess automated methods | Connect them to the search screen |
| SQL schema and tables | Primary owner | Uses the schema |
| API request module | Validates returned fields | Primary owner |
| Converting API responses to a shared format | Defines field requirements | Primary owner |
| Saving data to the database | Primary owner | Prepares API data |
| API keys and secret settings | Reviews secure storage approach | Connects them to the application environment |
| Data quality checks | Primary owner | API error checks |
| Annual totals and changes | Primary owner | Connects results to the interface |
| User interface | Defines requirements | Primary owner |
| Charts and filters | Validates calculations | Primary owner |
| Unit and integration tests | Database/analysis tests | API/interface tests |
| README and setup guide | Data and methodology sections | Setup and screen sections |
| Final presentation and demo | Together | Together |

### Team working rules

- Agree on database field names and the API's shared data format early.
- Do not change the schema without informing the other person.
- Develop each new feature in a separate Git branch where practical.
- Merge changes into the `main` branch only when they work and have been tested.
- Both people should understand the other person's code at a basic level.
- Never upload real API keys or passwords to GitHub.

---

## 13. Recommended project folder structure

The following structure is a starting recommendation and can be simplified as needed.

```text
turkiye-china-trade-explorer/
|-- app.py
|-- requirements.txt
|-- README.md
|-- .gitignore
|-- .env.example
|-- src/
|   |-- api_client.py
|   |-- database.py
|   |-- product_matching.py
|   |-- data_validation.py
|   `-- analysis.py
|-- sql/
|   |-- schema.sql
|   `-- analysis_queries.sql
|-- tests/
|   |-- test_database.py
|   |-- test_product_matching.py
|   |-- test_data_validation.py
|   `-- test_analysis.py
`-- docs/
    |-- data_dictionary.md
    |-- methodology.md
    |-- user_guide.md
    `-- decisions.md
```

### What the files do

- `app.py`: Starts the Streamlit interface.
- `api_client.py`: Communicates with the UN Comtrade API.
- `database.py`: Connects to the SQL database and manages data operations.
- `product_matching.py`: Matches product names with the catalog.
- `data_validation.py`: Checks for missing and inconsistent records.
- `analysis.py`: Calculates annual totals and changes.
- `schema.sql`: Defines the database tables.
- `analysis_queries.sql`: Contains important SQL analysis queries.
- `tests/`: Checks whether the code produces expected results.
- `docs/`: Stores the data dictionary, methodology, and usage explanations.

The `.env.example` file should contain only variable names and example placeholders; it must not contain a real API key or password.

---

## 14. Where will it run, and where will the data be stored?

### During development

Both team members can develop the code on their own computers. The code is shared through GitHub. Test data can be used locally, but real API keys and database passwords must not be added to the repository.

### Publishing online

The goal is for users to access the application even when your computer is turned off. To do this, the application runs on a hosting service and persistent data is stored in an online database.

Possible options for the first version:
- Python/Streamlit application: Streamlit Community Cloud or a similar hosting service
- Persistent SQL database: A cloud service based on PostgreSQL
- Code: GitHub
- Trade data: Retrieved from the UN Comtrade API when needed and cached appropriately

Free services may impose sleep behavior, resource and storage quotas, or limits on persistent files. Check the current conditions before deployment. A free tier may be sufficient for a small demo, but larger usage may incur costs.

### Will the data be on a computer or in the cloud?

- Code is developed on your and your teammate's computers and stored on GitHub.
- The production application runs on an online server.
- Persistent application data can be stored in a cloud PostgreSQL database.
- Results for repeated queries can be cached for reuse.
- Catalog files and test data can be kept locally during development.

This setup does not require your personal computer to stay on continuously.

---

## 15. Security and secrets

Treat the following rules as mandatory:

1. Do not write the API key directly into source code.
2. Do not upload the database password to GitHub.
3. Store secrets in the hosting service's secret/environment-variable settings.
4. Add the `.env` file to `.gitignore`.
5. Ensure `.env.example` contains no real secret information.
6. Do not collect unnecessary personal data from users.
7. Use parameterized SQL queries instead of directly concatenating user input into query text.
8. Limit database access to the permissions the application actually needs.
9. Ensure error messages do not expose API keys, passwords, or connection secrets.
10. Decide on database backup and recovery procedures before publishing.

---

## 16. Implementation stages: End-to-end roadmap

A first-version target of approximately 4–6 weeks may change depending on your current Python knowledge and the time you can devote each week. This is a planning estimate, not a guaranteed delivery date. It is normal to slow down during exam periods.

### Stage 0 — Lock the scope

**Goal:** Define the boundaries of the first version without adding unnecessary features.

Tasks:
- Confirm that no countries other than Türkiye and China will be included.
- Sketch the initial user flow.
- Select the data source and product classification.
- Choose the indicators to display in the first version.
- Read the data-use policy.

**Completion condition:** The team has written down what the first version will and will not do.

### Stage 1 — Validate the data source

**Goal:** Prove that access to real data works before making a large coding investment.

Tasks:
- Check UN Comtrade API access and the current terms of use.
- Select one product category.
- Test an appropriate query between Türkiye and China.
- Inspect the fields in the API response.
- Record the period and classification-version information.
- Test what happens when no data is found.

**Completion condition:** The API response for at least one selected product is understood, and the fields and query conditions are documented. This does not prove that data exists for all products.

### Stage 2 — Build the product catalog

**Goal:** Import product codes into the database without entering them manually.

Tasks:
- Find the official reference table.
- Decide which classification version to use.
- Obtain a file containing codes and descriptions.
- Inspect the file and import it into an SQL table.
- Validate the code, description, and version fields.
- Record the catalog update date.

**Completion condition:** The catalog can be searched, and the classification version for a product code is identifiable.

### Stage 3 — Database and SQL

**Goal:** Store and query data reliably.

Tasks:
- Design the `products`, `product_aliases`, `trade_records`, and `data_refresh_log` tables.
- Define primary-key and foreign-key relationships.
- Insert a few sample records into the database.
- Write filtering queries by country, product, period, and trade flow.
- Calculate annual totals with `GROUP BY` and `SUM`.
- Define a rule that prevents duplicate records.
- Prepare test queries.

**Completion condition:** Sample or verified records can be queried through SQL, and annual totals return the expected results.

### Stage 4 — API connection

**Goal:** Bring real data into the application.

Tasks:
- Write the API client module.
- Build parameters safely and consistently.
- Add timeout and error handling.
- Convert the API response into a common internal data format.
- Insert or update database records.
- Record the retrieval time.
- Reduce unnecessary repeated API calls.

**Completion condition:** A valid query retrieves data from the API, validates it, and saves it to the database; errors are handled without crashing the application.

### Stage 5 — Product search system

**Goal:** Match a product phrase in everyday language to an official product category.

Tasks:
- Implement exact-match search.
- Connect the alternative-name table.
- Add approximate text matching.
- Test Turkish, English, and Chinese examples.
- Display a selection screen when multiple results are found.
- Show an explanatory message when no match exists.

**Completion condition:** Common product searches in the test list return the expected results, and unknown phrases are handled safely.

### Stage 6 — Analysis and charts

**Goal:** Turn records into understandable findings.

Tasks:
- Calculate annual trade value.
- Calculate absolute and percentage change from the previous year.
- Identify missing periods.
- Keep value and quantity distinct.
- Create Plotly charts.
- Add source and methodology notes.

**Completion condition:** Chart values match SQL/Python calculations; missing data is not confused with a zero value.

### Stage 7 — User interface

**Goal:** Allow users to analyze the data without knowing technical details.

Tasks:
- Create the home page and search box.
- Add product-category selection.
- Add Türkiye–China filters.
- Add period selection.
- Display results tables and charts.
- Add source and limitation sections.
- Add messages for missing data and API errors.
- Create a simple, clear layout for mobile and desktop.

**Completion condition:** A user can complete the flow from product search to the results screen.

### Stage 8 — Testing and validation

**Goal:** Prevent an application that appears to work but produces incorrect results.

Tests:
- Is the product match correct?
- Can the user accidentally select the wrong product code?
- Is the Türkiye–China direction correct?
- Are imports and exports kept separate?
- Are annual totals calculated as expected?
- Is percentage change handled correctly when the previous year's data is missing?
- Can the same record be inserted twice?
- Does the user receive a clear message when the API fails?
- Is any secret visible in the source code?
- Does caching reduce unnecessary API requests?

**Completion condition:** Test results for the core scenarios are recorded, and known limitations are documented.

### Stage 9 — Publish online

**Goal:** Let users access the application without our computers being on.

Tasks:
- Organize the GitHub repository.
- Configure environment variables in the hosting service.
- Connect the cloud database.
- Deploy the application.
- Test searches and queries through the actual public URL.
- Check resource, sleep, and persistence limits on the free plan.
- Make usage and source information visible.

**Completion condition:** The application opens through a public link and core test scenarios work.

### Stage 10 — User feedback

**Goal:** Find out whether the application is genuinely useful.

Tasks:
- Show the prototype to a few target users.
- Ask whether product search is understandable.
- Test whether users understand what the results mean.
- Record which information users feel is missing.
- Set priorities for the next version.

**Completion condition:** There is a short improvement list based on real user feedback.

---

## 17. What will we not build in the first version?

To make it easier to finish the project, it makes sense to defer the following in the first version:

- A machine-learning model that predicts future trade values
- Automatic profitability calculations or investment recommendations
- Coverage of every country in the world
- Bulk downloads of raw-data archives by users
- A complex user-account and authorization system
- Paid subscriptions
- Perfect, unlimited multilingual product recognition from day one
- Thousands of manually written descriptions for every product
- Unnecessary second or third data sources

These can be considered later if a real need emerges. The first goal is to make the core product search and Türkiye–China analysis workflow reliable.

---

## 18. Risk register and mitigation plan

| Risk | Why it matters | Mitigation |
|---|---|---|
| Wrong product-code match | Incorrect trade data may be shown | Official catalog, classification version, user selection, and testing |
| Data is missing for some years | Missing records could be mistaken for zero | Explicitly identify missing data |
| Country-reported values differ | Comparison may be misinterpreted | Make the reporting country visible |
| API quota is exhausted | Data retrieval may temporarily fail | Caching and controlled requests |
| Source terms change | The publishing model may no longer be appropriate | Recheck terms before publication and when needed |
| Free hosting limits | The app may sleep or reach resource limits | Start with a small scope and change plans if needed |
| Multilingual search is weak | Users may get incorrect or no results | Alternative names, a test set, and uncertainty messages |
| API key is leaked | Others may use the quota | Server-side secrets, `.gitignore`, and access controls |
| Project grows and never ships | Too many features extend development | Stick to the first-version scope |
| Users see no value | A technically working product may go unused | Early user testing and feedback |

---

## 19. Success criteria

A project is not complete merely because a web page opens.

### Technical success
- The product catalog has been imported into the database.
- The search module offers the correct category options.
- The Türkiye–China API query works.
- Data can be saved to SQL and reused.
- Annual totals are calculated correctly.
- Missing data and error cases are handled.
- Secrets are stored securely.

### User success
- A user can search for a product.
- The user can understand the differences between product categories.
- The user can select the desired reporting perspective for Türkiye and China.
- The user can understand what the chart shows.
- The user can see the data source and limitations.

### Portfolio success
- The GitHub repository includes setup instructions.
- Code modules and division of responsibilities are explained.
- Tests are included.
- There are real screenshots and an example usage flow.
- The data source, methodology, and limitations are documented clearly.
- The project does not exaggerate what it can do and clearly states what it cannot do.

---

## 20. Recommended first-week checklist

These are the most important tasks to complete before writing large amounts of code.

- [ ] The Türkiye and China scope is finalized.
- [ ] Current UN Comtrade API and data-use conditions have been reviewed.
- [ ] API access and the current quota have been verified.
- [ ] One example product has been selected.
- [ ] The product's official code and classification version have been checked.
- [ ] An example query for Türkiye and China has been tested.
- [ ] Returned fields and possible gaps have been recorded.
- [ ] The initial product-catalog file has been identified.
- [ ] A draft SQL table design is ready.
- [ ] Each person's tasks have been added to GitHub Issues or a project board.
- [ ] No real result figures have been published before the first data query works.

Trying to build the whole application before this checklist is complete increases the risk that the data model will have to be changed later.

---

## 21. Value delivered to the end user

The user enters a product name, the system shows suitable official product categories, and the user explores Türkiye–China trade records for the selected category. The results are presented in annual tables and charts, with information about the source, reporting perspective, and data limitations.

The application aims to speed up preliminary research. On its own, it cannot tell the user which product will be profitable; it does not cover all the cost, competition, tax, supply, and demand data needed for that decision.

The project's value lies in making official data easier to find and interpret in the correct context. That value should be tested with real users.

---

## 22. Sources and documentation to verify

Use current, official documentation during development. Web pages and free-tier plans can change, so conditions should be checked again during API integration and deployment.

- **UN Comtrade portal:** https://comtradeplus.un.org/
- **UN Comtrade API documentation and help centre:** https://uncomtrade.org/docs/
- **World Customs Organization (WCO), Harmonized System:** https://www.wcoomd.org/en/topics/nomenclature/overview/what-is-the-harmonized-system.aspx
- **Streamlit documentation:** https://docs.streamlit.io/
- **Streamlit Community Cloud:** https://share.streamlit.io/
- **PostgreSQL documentation:** https://www.postgresql.org/docs/
- **Neon documentation and plans:** https://neon.tech/docs/
- **GitHub Docs:** https://docs.github.com/

### Points to keep in mind when using sources

- Verify the correct version of each HS code.
- Do not assume API field names; inspect a real response.
- Recheck the current free quota and terms of use.
- Account for data that may be missing or updated later.
- Reassess the data licence if the project moves toward commercial use.

---

## 23. Final recommendation

Trade Explorer is a feasible project for a two-person team to build for learning and portfolio purposes. The hardest part is not simply drawing charts; it is matching product names to the correct official classification, interpreting trade-data coverage properly, and presenting the results reliably.

It makes sense for you to take ownership of the SQL/data side. Your teammate can develop the API and interface. The data format, database schema, and tests should remain shared integration responsibilities.

**Recommended order:** First validate a real data query for one product; then create the product catalog and SQL tables; after that, proceed to API integration, search, analysis, interface, testing, and deployment.

**Goal for the first version:** A user enters a product name, selects a suitable category, filters trade to Türkiye and China only, and sees correctly calculated annual results with source information. Once this flow works reliably, adding more advanced features will make sense.
