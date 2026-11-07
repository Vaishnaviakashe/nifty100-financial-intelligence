# NIFTY 100 Financial Intelligence Platform

A financial research and analytics platform covering 92 NIFTY 100
companies. It combines financial data processing, KPI calculations,
screening, peer analysis, clustering, valuation intelligence, an
interactive dashboard and REST APIs.

## 1. Key Features

-   Financial data storage using SQLite.
-   ETL pipeline for loading, normalising and validating financial
    records.
-   Financial ratios, profitability, leverage and growth analytics.
-   Six predefined financial screener strategies.
-   Peer-group percentile rankings across ten metrics.
-   KMeans clustering into five company archetypes.
-   Cash-flow and capital-allocation intelligence.
-   Valuation analysis and portfolio statistics.
-   Streamlit dashboard with eight analyst screens.
-   FastAPI REST API with 18 documented paths.
-   Automated tests and PDF company tearsheets.

## 2. Technology Stack

  Component          Technology
  ------------------ -----------------------------
  Programming        Python 3.10
  Data analysis      Pandas, NumPy
  Database           SQLite
  Dashboard          Streamlit
  API                FastAPI
  Visualisation      Plotly, Matplotlib, Seaborn
  Machine learning   Scikit-learn
  Testing            Pytest
  Code quality       Black, Ruff

## 3. Project Structure

``` text
nifty100/
├── data/
│   └── nifty100.db
├── docs/
│   ├── analyst_guide.pdf
│   └── openapi.json
├── output/
├── reports/
│   └── tearsheets/
├── scripts/
├── src/
│   ├── analytics/
│   ├── api/
│   ├── dashboard/
│   ├── etl/
│   ├── nlp/
│   └── reports/
├── tests/
├── README.md
└── requirements.txt
```

## 4. Installation

Open PowerShell in the project root.

``` powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Ensure the database exists at `data/nifty100.db`.

## 5. ETL Pipeline

The ETL modules are:

-   `src/etl/loader.py` --- loads source financial workbooks.
-   `src/etl/normaliser.py` --- normalises company identifiers and
    financial periods.
-   `src/etl/validator.py` --- validates financial records and data
    quality.

The pipeline loads source data, standardises fields, validates records
and stores the resulting data in SQLite.

ETL orchestration scripts are maintained under `scripts/`. Back up the
database before running database-writing operations.

## 6. Running the Dashboard

``` powershell
streamlit run src/dashboard/app.py
```

Open `http://localhost:8501`.

The dashboard contains:

1.  Home
2.  Company Profile
3.  Screener
4.  Peers
5.  Trends
6.  Sectors
7.  Capital
8.  Reports

## 7. Running the REST API

``` powershell
uvicorn src.api.main:app --host 127.0.0.1 --port 8000 --reload
```

API base URL: `http://127.0.0.1:8000`

Interactive documentation: `http://127.0.0.1:8000/docs`

## 8. API Endpoints

  Endpoint                                     Purpose
  -------------------------------------------- --------------------------------
  `/api/v1/health`                             API and database health
  `/api/v1/companies`                          Company listing
  `/api/v1/companies/{ticker}`                 Company profile
  `/api/v1/companies/{ticker}/pl`              Profit and loss history
  `/api/v1/companies/{ticker}/bs`              Balance sheet history
  `/api/v1/companies/{ticker}/cashflow`        Cash-flow history
  `/api/v1/companies/{ticker}/ratios`          Financial ratios
  `/api/v1/companies/{ticker}/tearsheet`       PDF tearsheet
  `/api/v1/screener`                           Financial screening
  `/api/v1/sectors`                            Sector summaries
  `/api/v1/sectors/{sector}/companies`         Sector companies
  `/api/v1/peers/{group_name}`                 Peer rankings
  `/api/v1/companies/{ticker}/peers/compare`   Peer comparison
  `/api/v1/market-cap/{ticker}`                Historical valuation multiples
  `/api/v1/portfolio/stats`                    Portfolio statistics
  `/api/v1/companies/{ticker}/documents`       Company documents
  `/api/v1/valuation/summary`                  Valuation summary

Consult `/docs` for the live API schema and supported parameters.

### Example requests

``` powershell
curl.exe "http://127.0.0.1:8000/api/v1/health"
curl.exe "http://127.0.0.1:8000/api/v1/companies"
curl.exe "http://127.0.0.1:8000/api/v1/companies/TCS"
curl.exe "http://127.0.0.1:8000/api/v1/companies/TCS/ratios"
curl.exe "http://127.0.0.1:8000/api/v1/screener?preset=quality"
curl.exe "http://127.0.0.1:8000/api/v1/portfolio/stats"
```

## 9. Financial Analytics

### Screener Presets

  -----------------------------------------------------------------------
  Preset                              Conditions
  ----------------------------------- -----------------------------------
  Quality                             ROE \>= 15%, ROCE \>= 15%, net
                                      margin \>= 10%

  Low Debt                            Debt/equity \<= 0.5, interest
                                      coverage \>= 3

  Cash Generators                     Positive FCF, CFO quality \>= 1

  High Returns                        ROE \>= 20%, ROCE \>= 20%

  Efficient                           Asset turnover \>= 0.75, OPM \>=
                                      15%

  Balanced                            Net margin \>= 10%, ROE \>= 12%,
                                      debt/equity \<= 1, positive FCF
  -----------------------------------------------------------------------

### Peer Engine

Calculates percentile rankings across ten financial metrics within
eleven peer groups.

### Clustering

Uses KMeans to group companies into five archetypes using selected
profitability, leverage and growth indicators.

### Valuation

Includes FCF yield, valuation flags and historical valuation multiples
where data is available.

## 10. Reports and Outputs

Important project outputs include:

-   `output/cluster_labels.csv`
-   `output/outlier_report.csv`
-   `output/portfolio_stats.csv`
-   `reports/tearsheets/`
-   `reports/correlation_heatmap.png`
-   `reports/pytest_report.html`
-   `docs/analyst_guide.pdf`
-   `docs/openapi.json`

The Analyst Guide provides detailed usage instructions, methodology, API
examples and troubleshooting guidance.

## 11. Testing and Code Quality

Run the complete test suite:

``` powershell
pytest -v
```

Generate an HTML test report:

``` powershell
pytest -v --html=reports/pytest_report.html
```

Format code:

``` powershell
python -m black src tests scripts
```

Run lint checks:

``` powershell
python -m ruff check src tests scripts
```

### Recorded Day 44 Results

-   Black formatting: Passed.
-   Ruff lint: All checks passed.
-   Pytest: 143 passed.
-   Two dependency deprecation warnings.

Re-run these checks after subsequent code changes.

## 12. Data Quality and Limitations

The reviewed database snapshot contained:

-   92 companies.
-   1,073 financial ratio records.
-   11 peer groups.
-   521 generated pros/cons signals: 432 pros and 89 cons.
-   50 companies with at least one generated pro and one con.

Known limitations:

-   The financial ratio count is below the target of 1,100.
-   Some companies have incomplete or missing financial history.
-   ATGL had no cash-flow data in the reviewed snapshot.
-   Some analysis records were unmatched or unavailable.
-   Extreme ROE values require individual investigation.
-   Cash-flow quality and capital-allocation labels are heuristic
    indicators.

Missing data must not be replaced with fabricated zero values. Analysts
should verify source filings and apply sector-specific judgement.

## 13. Disclaimer

This platform is intended for financial research, analytics and
educational purposes. It does not constitute investment advice or a
recommendation to buy or sell securities. All financial outputs should
be independently verified before use.

------------------------------------------------------------------------

**Project:** NIFTY 100 Financial Intelligence Platform\
**Documentation:** `docs/analyst_guide.pdf`\
**Last updated:** 07 November 2026
