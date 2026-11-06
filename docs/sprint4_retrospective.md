# Sprint 4 Retrospective — Dashboard and Valuation

## Sprint objective
Deliver an interactive Streamlit dashboard and a valuation workflow for the NIFTY 100 Financial Intelligence Platform.

## Planned scope
- Eight dashboard pages: Home, Company Profile, Financial Screener, Peer Comparison, Trend Analysis, Sector Analysis, Capital Allocation and Annual Reports.
- Valuation calculations and classification.
- Excel and CSV exports.
- Integration testing, documentation and sprint closure.

## Delivered
- Implemented eight Streamlit page scripts.
- Added shared dashboard data-access functions.
- Applied navy, orange and white visual styling with Times New Roman typography.
- Implemented valuation analytics using stored market-capitalisation and financial-ratio data.
- Generated `output/valuation_summary.xlsx` and `output/valuation_flags.csv`.
- Integrated valuation distribution and company-level results into Financial Screener.

## Validation evidence

### Valuation outputs
- 92 rows and 92 unique company IDs.
- No missing values in the exported summary columns at the recorded checkpoint.
- Classification: 48 Fair, 30 Discount and 14 Caution.
- Flagged CSV: 44 companies (30 Discount and 14 Caution).

### Automated tests
- Existing test suite: 76 passed.

### Data-layer smoke check
- 92 companies and 92 unique IDs loaded.
- 11 peer groups loaded.
- Company history queries returned records for the sampled company.
- Sector data loaded for 92 companies across 10 broad sectors.
- 1,457 annual-report records retrieved; 1,109 URL strings had an HTTP/HTTPS prefix.

The data-layer check ran outside the Streamlit runtime and emitted bare-mode cache/runtime warnings, but completed. URL prefix validation does not establish external link reachability.

## Challenges and observations
- Financial year values use a `YYYY-MM` format; queries must extract the year component.
- Historical coverage varies by company and metric.
- Annual-report records include entries without HTTP/HTTPS URLs.
- Streamlit cache calls outside its runtime emit expected bare-mode warnings.
- Implementation and visual polish must be balanced against integration testing.

## What went well
- Existing automated tests remained green at the validation checkpoint.
- Valuation outputs covered all 92 company records.
- Shared data-access functions reduced repeated SQL logic.
- Valuation exports are reproducible from the stored database.

## Improvements for the next sprint
- Add automated tests for dashboard data access and valuation edge cases.
- Add repeatable annual-report link validation.
- Improve wide-table usability.
- Add explicit data freshness and coverage indicators.
- Keep generated outputs and local environment files separate from source-controlled code.

## Closure checklist
- [x] Eight dashboard page scripts implemented.
- [x] Valuation engine executed.
- [x] Excel and CSV outputs generated.
- [x] Valuation output validation passed.
- [x] Existing test suite passed (76 tests).
- [ ] Final browser check of all pages after latest edits.
- [ ] Verify external annual-report links.
- [ ] Review README and repository contents.
- [ ] Confirm `.env` and local database handling in `.gitignore`.
- [ ] Commit and push final sprint changes.

## Conclusion
Sprint 4 delivered the dashboard implementation and valuation workflow, with successful valuation-output validation and a passing existing test suite. Complete the remaining browser, external-link and Git hygiene checks before treating the repository publication as final.
