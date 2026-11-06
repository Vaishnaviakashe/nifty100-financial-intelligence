# NIFTY 100 Financial Intelligence Platform

A Python-based financial analytics platform covering 92 NIFTY 100 company records. It combines a SQLite database, financial analytics, screening, peer analysis, valuation indicators and an interactive Streamlit dashboard.

## Features

- Financial data foundation and SQLite storage.
- Financial ratio and company-level analytics.
- Fundamental screener with presets, filters and CSV export.
- Peer-group comparison and percentile analysis.
- Historical trend and sector analysis.
- Rule-based capital-allocation pattern classification.
- Annual-report records and available external links.
- Relative valuation using P/E, P/B, EV/EBITDA and FCF yield.
- Excel and CSV valuation exports.

## Dashboard pages

1. Home — market overview, KPIs, sector distribution and quality ranking.
2. Company Profile — company fundamentals and historical performance.
3. Financial Screener — financial filters, presets and CSV export.
4. Peer Comparison — peer-group comparisons and benchmarks.
5. Trend Analysis — historical financial metrics.
6. Sector Analysis — sector metrics and revenue-versus-ROE analysis.
7. Capital Allocation — heuristic capital-allocation patterns.
8. Annual Reports — report records and available links.

The Financial Screener also includes a Valuation Intelligence section.

## Technology

Python, Pandas, NumPy, SQLite, Streamlit, Plotly, OpenPyXL and Pytest.

## Repository structure

```text
nifty100/
├── config/
├── data/
├── db/
├── docs/
├── notebooks/
├── output/
├── pages/
├── reports/
├── scripts/
├── src/
│   ├── analytics/
│   ├── dashboard/
│   └── etl/
├── tests/
├── .streamlit/
├── requirements.txt
└── README.md
```

## Setup

```powershell
git clone https://github.com/Vaishnaviakashe/nifty100-financial-intelligence.git
cd nifty100-financial-intelligence
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

If environment variables are required, copy `.env.template` to `.env` and populate the required values. Never commit `.env` or credentials.

The dashboard expects the project SQLite database at `data/nifty100.db`. Use the project's ETL/database setup process if it is not present.

## Run the dashboard

```powershell
streamlit run src/dashboard/app.py
```

Open the local URL printed by Streamlit (normally `http://localhost:8501`).

## Run valuation exports

```powershell
python scripts/run_valuation.py
```

The current runner is configured for FY 2024. It generates:

- `output/valuation_summary.xlsx`
- `output/valuation_flags.csv`

### Valuation methodology

- FCF yield = latest available free cash flow / latest available market capitalisation × 100.
- Five-year median P/E = median of up to the latest five available annual P/E observations up to the selected year.
- Sector median P/E = median of positive latest P/E values among companies in the same broad sector.
- Discount = company P/E below 70% of sector median.
- Fair = company P/E between 70% and 150% of sector median.
- Caution = company P/E above 150% of sector median.
- Missing/non-positive P/E or unavailable sector median is treated as insufficient data.

These are relative screening indicators, not investment recommendations. Outputs use stored project data and are not live market quotes.

## Run tests

```powershell
pytest -q
```

At the recorded Sprint 4 validation checkpoint, the existing test suite reported **76 passed**. Re-run tests after changes and before publishing.

## Data interpretation notes

- Historical coverage varies by company and metric.
- Missing values must not be interpreted as zero.
- Capital-allocation labels are heuristic classifications based on available financial indicators, not audited disclosures of management's use of funds.
- Annual-report links are sourced from the database. A syntactically valid URL does not prove the external document remains accessible.
- Valuation flags are not standalone buy/sell advice.

## Recorded Sprint 4 validation

- Eight dashboard page scripts implemented.
- Valuation engine executed for 92 companies.
- Valuation summary contained 92 unique companies with no missing output values at the validation checkpoint.
- Classification: 48 Fair, 30 Discount and 14 Caution.
- `valuation_summary.xlsx` and `valuation_flags.csv` generated.
- Existing automated test suite: 76 passed.
- Data-layer smoke check loaded 92 companies and 11 peer groups; 1,457 annual-report records were retrieved.

See `docs/` for architecture, sprint retrospectives and the demo guide. Before a public release, rerun tests, inspect Git status, confirm database distribution/licensing and verify that no secrets or local-only files are committed.
