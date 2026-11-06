# Sprint 2 Retrospective — Ratio Engine

## Completed

Sprint 2 implemented the core financial ratio engine and connected the calculations to the SQLite database.

Completed areas:

- Profitability ratios
- Leverage ratios
- Efficiency ratios
- CAGR calculation functions
- Cash-flow KPIs
- Capital allocation classification
- Financial ratio database population
- Banks/NBFC ROCE cross-check
- Automated KPI tests
- Edge-case documentation

## Database

The `financial_ratios` table was rebuilt and populated from the available source data.

Current population:

- Companies: 92
- Financial ratio rows: 1,073
- Source `profitandloss` rows: 1,073
- All available source company-year records were populated.

The project specification mentions a 1,184+ row target based on 92 companies × 14 years. However, the supplied source data does not contain 14 years of history for every company. Several companies have fewer historical records, including JIOFIN (2), LICI (6), ATGL (7), ADANIGREEN (8), BAJFINANCE (10), and others.

Therefore, 1,073 is the maximum population supported by the supplied source `profitandloss` data, and no artificial rows were created for unavailable years.

## Outputs

Generated Sprint 2 outputs include:

- `data/nifty100.db`
- `output/capital_allocation.csv`
- `output/sector_roce_notes.csv`
- `output/ratio_edge_cases.log`

## Testing

The complete current test suite passes:

**72 tests passed**

This confirms that the implemented KPI functions and related validation tests are currently passing.

## Key Observations

The OPM calculation was cross-checked against the source `opm_percentage` field. Small differences were observed because the source values are rounded.

The Banks/NBFC ROCE cross-check also showed differences between the calculated year-level ROCE and the company-level `roce_percentage` source field. These differences were documented rather than treating them automatically as calculation failures.

## Lessons Learned

- Financial ratios require explicit handling of division-by-zero cases.
- Different source systems may calculate the same financial metric using different methodologies.
- Company-level metrics should not automatically be treated as equivalent to year-level calculations.
- Automated tests are important for protecting KPI calculations from formula and edge-case errors.
- Database validation should be performed after every major ETL or analytics step.

## Sprint 2 Exit Validation

- Ratio calculations implemented: Yes
- Database population completed: Yes
- Capital allocation output generated: Yes
- Sector ROCE cross-check completed: Yes
- Automated tests passing: Yes
- Edge cases documented: Yes