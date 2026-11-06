# Demo Guide — NIFTY 100 Financial Intelligence Platform

## Before the demo

```powershell
.\venv\Scripts\Activate.ps1
pytest -q
python scripts/run_valuation.py
streamlit run src/dashboard/app.py
```

Confirm the dashboard opens and the valuation workbook and CSV exist in `output/`.

## Suggested 6–8 minute walkthrough

1. **Home:** introduce the 92-company universe, market KPIs, sector distribution and quality ranking.
2. **Company Profile:** search a company and explain available KPIs and historical charts.
3. **Financial Screener:** select a preset, adjust filters, show results and CSV export; then open Valuation Intelligence.
4. **Peer Comparison:** select a peer group and show member companies, comparisons and benchmark statistics.
5. **Trend Analysis:** select a company and metrics; explain the historical chart.
6. **Sector Analysis:** show sector medians and revenue-versus-ROE bubble chart.
7. **Capital Allocation:** show pattern distribution and explain that categories are heuristic.
8. **Annual Reports:** filter records and open an available external report link if reachable.
9. **Valuation outputs:** show `output/valuation_summary.xlsx`, explain FCF yield and sector-relative P/E flags, and show the flagged-company CSV.

## Closing statement

The platform brings company fundamentals, screening, peer analysis, historical trends, sector views, annual-report records and relative valuation into one analytical workflow.

## Demo cautions

- Do not describe stored data as live market data.
- Discount is not a guaranteed undervaluation or buy recommendation.
- Capital-allocation categories are not verified management disclosures.
- Annual-report links may be expired or unavailable.
