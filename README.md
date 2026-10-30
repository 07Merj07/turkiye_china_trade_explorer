# Türkiye–China Trade Explorer

**A Collaborative Türkiye–China Project**

**Developed by:**
- **Mert Can Yalçın** 🇹🇷 — Türkiye
- **Tao Jingchu** 🇨🇳 — China

---

A Streamlit application for exploring reported merchandise exports between Türkiye and China by HS product code and year. The application reads stored trade records and the product catalogue from a Neon PostgreSQL database.

## What the MVP Currently Does

- Search the product catalogue by HS code or product-description text.
- Select one of the supported trade directions:
  - Türkiye → China (Türkiye-reported exports)
  - China → Türkiye (China-reported exports)
- Select a year range currently supported by the application (2019–2025).
- View annual trade values, year-over-year (YoY) changes, and charts.
- Compare the two reporting perspectives.
- Review data availability and methodology notes.

**Important:** The two directions are separate reporting perspectives. They can differ because of reporting coverage, timing, valuation, and classification practices. Do not add them together or treat them as exact mirror values.

## Technology

- Python
- Streamlit
- Pandas
- Plotly
- PostgreSQL hosted on Neon
- Psycopg
- python-dotenv

## Project Files

- `app.py` — Streamlit user interface and application flow.
- `database_neon.py` — Neon PostgreSQL connection, product search, and trade-series queries.
- `analysis.py` — annual-series and analytical calculations.
- `charts.py` — Plotly chart functions.
- `requirements.txt` — Python dependencies.
- `.env.example` — safe template for the local database connection setting.

Older modules such as SQLite/API prototypes may remain in the repository for development history. The current Streamlit app uses `database_neon.py`; do not delete older files until their references and purpose have been checked.

## Setup

### 1. Get the Project

Clone the repository or download the project files.

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd <PROJECT_FOLDER>
```

### 2. Create and Activate a Virtual Environment

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install Dependencies

```powershell
python -m pip install -r requirements.txt
```

### 4. Configure the Database Connection

Copy `.env.example` to `.env` and put your own Neon PostgreSQL connection string in `.env`.

Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Open `.env` and replace the placeholder value of `DATABASE_URL`.

**Never upload `.env` or share the real database URL.** The `.gitignore` file excludes it from Git.

### 5. Run the Application

```powershell
streamlit run app.py
```

The application should open in your browser at the local Streamlit address, usually `http://localhost:8501`.

## Data Source and Database

The stored trade records originate from UN Comtrade data imported into the project's Neon PostgreSQL database. The application currently displays USD values filtered to FOB valuation.

The project database has been checked for the current loaded snapshot:

- Trade records: 54,312
- Product catalogue records: 6,939
- Trade years: 2019–2025
- HS5 records: 21,834
- HS6 records: 32,478
- Duplicate groups under the checked record dimensions: 0
- Missing required trade fields in the checked columns: 0
- Negative trade values: 0

These are results for the database snapshot that was checked, not a guarantee about future imports or every possible query.

## Methodology and Limitations

- `TUR` is Türkiye and `CHN` is China.
- Türkiye → China uses Türkiye as reporter and China as partner, with export flow.
- China → Türkiye uses China as reporter and Türkiye as partner, with export flow.
- Values shown by the current application are USD and filtered to FOB valuation.
- A missing year is treated as missing data, not as zero.
- The application stops when it detects multiple matching records for the same selected product, direction, and year rather than silently summing potentially overlapping rows.
- The product catalogue uses HS2022, while trade records use H5 for 2019–2021 and H6 for 2022–2025. Historical code equivalence is not guaranteed for every product. HS concordance must be checked before making strict long-term product comparisons.
- Reporter-country export data and partner-country mirror records may differ. The app displays the reporting perspective rather than forcing the two sources to match.
- The current application period is 2019–2025. Do not assume earlier years or future years are available.
- This is a historical trade-data exploration tool. It does not predict profitability, consumer demand, future sales, customs costs, or supplier reliability.

## Security

- Keep real credentials in `.env` locally.
- Do not commit `.env`, database passwords, API keys, or Streamlit secrets.
- For online deployment, configure `DATABASE_URL` in the hosting provider's secret/environment-variable settings.
- Use a database role with only the permissions the application needs.

## Team & Contributors

Both contributors collaborate on project architecture, data methodology, testing, and overall development decisions.

The project aims to provide a transparent and data-driven exploration of bilateral trade between Türkiye and China.

## Current Project Status

The local MVP has been launched and manually checked for product search, Neon connectivity, both trade directions, annual values, YoY view, comparison view, data table, and methodology view.

A complete automated test suite and public deployment have not been confirmed yet.