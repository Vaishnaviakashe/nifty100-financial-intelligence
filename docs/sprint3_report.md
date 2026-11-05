# Sprint 3 – Financial Screener and Peer Engine

## 1. Sprint Overview

**Sprint:** 3  
**Duration:** Day 15–21  
**Epics:** Epic 03 – Financial Screener; Epic 04 – Peer Engine  
**Status:** Implementation completed and tests passed.

## 2. Sprint Objectives

- Develop six preset financial screening filters.
- Calculate financial metric percentiles within peer groups.
- Rank companies against their respective peers.
- Export screening and peer-ranking results as CSV files.

## 3. Financial Screener

Implemented in: `src/analytics/screener.py`

Six screening presets:

| Preset | Description | Companies Matched |
|---|---|---:|
| Quality | Profitability and return metrics | 30 |
| Low Debt | Lower debt and stronger interest coverage | 46 |
| Cash Generators | Positive free cash flow and CFO quality | 40 |
| High Returns | Higher ROE and ROCE | 30 |
| Efficient | Asset turnover and operating margin | 23 |
| Balanced | Combined profitability, returns, debt and cash flow | 28 |

Each preset uses the latest available financial-ratio record for each company.

## 4. Peer Comparison Engine

Implemented in: `src/analytics/peer_engine.py`

The peer engine:
- Compares 56 companies across 11 peer groups.
- Calculates percentile rankings for 10 financial metrics.
- Uses higher-is-better ranking for positive financial metrics.
- Uses lower-is-better ranking for debt-to-equity.
- Calculates an overall percentile and overall rank for each company.
- Exports the results to `output/peer_rankings.csv`.

### Peer Groups

Automobiles, Consumer Finance, FMCG, IT Services, Life Insurance, Oil & Gas, Pharmaceuticals, Power & Utilities, Private Banks, Public Sector Banks and Steel.

### Top-ranked companies

| Peer Group | Top-ranked Company |
|---|---|
| Automobiles | HEROMOTOCO |
| Consumer Finance | BAJFINANCE |
| FMCG | HINDUNILVR |
| IT Services | TCS |
| Life Insurance | LICI |
| Oil & Gas | ONGC |
| Pharmaceuticals | CIPLA, TORNTPHARM |
| Power & Utilities | ADANIPOWER |
| Private Banks | KOTAKBANK |
| Public Sector Banks | CANBK |
| Steel | HINDALCO |

Some peer groups have tied leaders.

## 5. Generated Deliverables

### Source Code
- `src/analytics/screener.py`
- `src/analytics/peer_engine.py`
- `scripts/run_screener.py`
- `scripts/run_peer_analysis.py`
- `tests/test_sprint3.py`

### Output Files
- `output/screener_quality.csv`
- `output/screener_low_debt.csv`
- `output/screener_cash_generators.csv`
- `output/screener_high_returns.csv`
- `output/screener_efficient.csv`
- `output/screener_balanced.csv`
- `output/peer_rankings.csv`

## 6. Testing and Validation

Dedicated Sprint 3 tests cover:
- All six screener presets.
- Invalid preset handling.
- Peer-ranking output.
- Overall percentile and rank validation.

**Final test execution:**

`pytest -q`

**Result: 76 passed in 1.40 seconds.**

## 7. Known Limitations

- Peer percentile rankings are relative to the companies included in each peer group.
- Absolute free cash flow can favor larger companies.
- Financial data quality and missing values can affect individual metric rankings.
- Tied percentile scores can produce multiple top-ranked companies.
- Rankings should be interpreted as analytical comparisons, not investment recommendations.

## 8. Sprint Outcome

Sprint 3 successfully implemented the financial screener and peer comparison engine. Six preset screening outputs and one peer-ranking output were generated. The complete test suite passed with 76 tests.

**Sprint 3 implementation: Completed.**
