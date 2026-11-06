# Platform Architecture

## High-level flow

```text
Source financial datasets
        |
        v
ETL and data validation
        |
        v
SQLite database (nifty100.db)
        |
        +-------------------------------+
        |                               |
        v                               v
Analytics modules                 Dashboard data access
(ratios, screener, peers,          (SQLite queries and
valuation, sector analysis)         cached data functions)
        |                               |
        v                               v
CSV / Excel outputs               Streamlit + Plotly
                                        |
                                        v
                                Eight dashboard pages
```

## Layers

### Data layer
SQLite stores company, sector, financial statement, ratio, market-capitalisation, stock-price, peer-group and annual-report records.

### ETL layer
ETL modules ingest and normalize source datasets, validate records and populate the database. See the existing Sprint 1 retrospective for the data-foundation work.

### Analytics layer
Analytics modules calculate financial metrics, screening rules, peer comparisons and valuation indicators.

### Dashboard layer
The Streamlit application uses shared data-access functions in `src/dashboard/utils/` and page scripts in the root `pages/` directory. Plotly renders interactive charts.

### Outputs
Analytical deliverables are written to `output/`, including screener exports, peer rankings, capital-allocation classifications and valuation reports.

## Valuation workflow

1. Read company universe and sector mapping.
2. Select latest market-cap record up to the selected year.
3. Select latest financial-ratio record up to the selected year.
4. Calculate FCF yield when market capitalisation is positive and FCF is available.
5. Calculate the median of up to five latest annual P/E observations per company.
6. Calculate sector median P/E from positive latest company P/E values.
7. Assign Discount, Fair, Caution or Insufficient Data.
8. Export the summary workbook and flagged-company CSV.

## Boundaries and caveats

- Stored project data is not live market data.
- Missing values must remain distinguishable from zero.
- Annual-report URL reachability requires external link checking.
- Capital-allocation labels are heuristic, not direct evidence of cash deployment.
