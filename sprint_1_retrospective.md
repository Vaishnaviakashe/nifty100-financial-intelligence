# Sprint 1 Retrospective — NIFTY 100 Financial Intelligence Platform

## Sprint Goal

Build a reliable data foundation by loading the Nifty 100 financial datasets into a validated SQLite database and establishing the foundation for downstream analytics.

---

## 1. Sprint Summary

Sprint 1 focused on building the data foundation for the NIFTY 100 Financial Intelligence Platform.

The sprint covered:

- Project and Python environment setup
- Excel data loading and normalization
- Data-quality validation
- SQLite database schema creation
- ETL pipeline development
- Loading core and supplementary datasets
- Foreign-key and duplicate validation
- Manual database checks
- Exploratory SQL analysis

The final database contains 12 populated tables covering company information, financial statements, market data, sectors, financial ratios, and peer groups.

---

## 2. What Was Completed

### Day 1 — Environment Setup

Completed:

- Project directory structure
- Python virtual environment
- Required dependencies
- Environment configuration
- Development tooling

### Day 2 — Excel Loader and Normalization

Implemented:

- Excel loading through Pandas
- Separate handling for core and supplementary datasets
- `normalize_year()`
- `normalize_ticker()`
- Annual-data deduplication
- Unit tests for normalization

Validation:

- 35 normalization tests passed.

### Day 3 — Data Quality Validation

Implemented the project's data-quality validation framework covering the defined DQ rules.

Important findings included:

- Duplicate annual records
- Orphan company IDs
- Unparseable year values
- Missing financial values
- OPM mismatches
- Tax-rate and dividend-payout warnings
- Document URL validation warnings
- Coverage warnings

Critical validation findings were investigated and addressed during the loading process.

### Day 4 — SQLite Schema

Created the SQLite database schema with:

- Primary keys
- Foreign keys
- Financial statement tables
- Company master data
- Supporting datasets

The schema was adjusted where necessary to accommodate valid source-data NULL values.

### Day 5 — ETL and Database Loading

Loaded the available core and supplementary datasets into SQLite.

Final table counts:

| Table | Rows |
|---|---:|
| companies | 92 |
| profitandloss | 1,073 |
| balancesheet | 1,140 |
| cashflow | 1,056 |
| analysis | 16 |
| documents | 1,457 |
| prosandcons | 14 |
| sectors | 92 |
| stock_prices | 5,520 |
| market_cap | 552 |
| financial_ratios | 1,041 |
| peer_groups | 56 |

Foreign-key validation completed successfully with no remaining FK violations.

### Day 6 — Database Validation

Performed additional checks on the loaded database.

Verified:

- No duplicate company-year records in P&L, Balance Sheet, and Cash Flow
- No remaining `PARSE_ERROR` years in P&L
- No orphan company IDs in P&L
- Foreign-key integrity
- Database table and row counts

### Day 7 — Exploratory SQL

Created `exploratory_queries.sql` and executed exploratory SQL against the SQLite database.

Key findings:

- 92 companies are present.
- P&L coverage ranges from `2011-03` to `2024-09`.
- JIOFIN currently has fewer than five P&L years, with 2 years available.
- Sales and net profit contain no NULL values in the loaded P&L data.
- 12 operating-profit values and 4 EPS values are NULL.
- Financials is the largest broad sector with 23 companies.
- Financial-ratio data contains substantial historical coverage.
- 1,058 company-year records have matching P&L and Balance Sheet records.

---

## 3. Data Quality Decisions

Several data-quality issues were handled during the ETL process rather than modifying the raw source files.

### Duplicate annual records

Duplicate company-year records were identified in annual financial datasets.

The loading process retained the last occurrence for valid company-year combinations and recorded the number of removed duplicate rows in the audit.

### Invalid year values

Unparseable year values were identified and excluded from database loading.

The raw source files were not modified.

### Orphan company IDs

Rows whose `company_id` did not exist in the company master table were excluded from database loading.

The affected rows were tracked through the validation and load-audit process.

### Missing financial values

Valid source-data NULL values were preserved where the database schema allowed them.

They were not automatically converted to zero because NULL and zero represent different meanings in financial data.

---

## 4. What Went Well

- The project structure remained organized as the pipeline expanded.
- Normalization functions were separated from loading logic.
- Automated tests were created for normalization.
- Data-quality rules were explicitly defined and executed.
- Raw source files were preserved without modification.
- SQLite foreign-key constraints helped verify referential integrity.
- The ETL process generated a load audit.
- Exploratory SQL provided a quick way to verify the loaded database.

---

## 5. What Was Challenging

The main challenges during Sprint 1 were:

1. Different Excel files required different header handling.
2. Financial-year values appeared in multiple formats.
3. Some datasets contained duplicate company-year records.
4. Several source datasets contained company IDs that were not present in the master company table.
5. Some financial fields contained valid NULL values.
6. URL validation generated a large number of warnings that required interpretation.
7. The database schema had to reflect the actual source data rather than assuming every field would always be populated.

---

## 6. Lessons Learned

This sprint demonstrated that ETL is not simply about moving data from Excel into a database.

Important lessons learned:

- Raw data should be preserved.
- Data should be normalized before analysis.
- Validation rules should be explicit and reproducible.
- Primary-key and foreign-key integrity are essential.
- NULL values should be interpreted carefully.
- Financial data requires domain-aware validation.
- A database load should produce an audit trail.
- Exploratory SQL is useful for checking whether the resulting database makes sense.

---

## 7. Sprint Outcome

Sprint 1 established the data foundation required for subsequent analytics work.

The SQLite database is populated, normalization and validation processes are in place, foreign-key integrity has been checked, and exploratory SQL confirms that the loaded data can be queried across multiple financial and supporting datasets.

Critical data-quality issues identified during validation were addressed before database sign-off.

---

## 8. Next Sprint Focus

The next sprint can build on this foundation by focusing on analytical processing and financial intelligence, including:

- financial ratios
- growth and CAGR calculations
- company comparisons
- sector-level analysis
- valuation analysis
- trend analysis
- downstream dashboards and reporting