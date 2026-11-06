"""Run valuation analytics and export Sprint 4 deliverables."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.analytics.valuation import export_valuation_outputs

if __name__ == "__main__":
    year = 2024
    summary, xlsx, csv = export_valuation_outputs(year=year)
    print("\\nVALUATION ENGINE COMPLETED")
    print(f"Financial year: FY {year}")
    print(f"Companies processed: {len(summary)}")
    print("\\nFlag distribution:")
    print(summary["valuation_flag"].value_counts().to_string())
    print(f"\\nExcel output: {xlsx}")
    print(f"CSV output: {csv}")
