"""Run data quality validation for the Nifty 100 core datasets."""

from pathlib import Path

import pandas as pd

from src.etl.loader import load_excel
from src.etl.validator import run_all_validations


BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"
OUTPUT_DIR = BASE_DIR / "data" / "processed"

CORE_FILES = {
    "companies": "companies.xlsx",
    "profitandloss": "profitandloss.xlsx",
    "balancesheet": "balancesheet.xlsx",
    "cashflow": "cashflow.xlsx",
    "analysis": "analysis.xlsx",
    "documents": "documents.xlsx",
    "prosandcons": "prosandcons.xlsx",
}

def load_core_datasets() -> dict[str, pd.DataFrame]:
    """Load all seven core Excel datasets."""

    datasets = {}

    for name, filename in CORE_FILES.items():
        path = RAW_DIR / filename

        print(f"Loading {filename}...")

        datasets[name] = load_excel(
            path,
            core=True,
        )

    return datasets


def main() -> None:
    """Run all data quality checks and save failures."""

    datasets = load_core_datasets()

    failures = run_all_validations(
        companies=datasets["companies"],
        profitandloss=datasets["profitandloss"],
        balancesheet=datasets["balancesheet"],
        cashflow=datasets["cashflow"],
        documents=datasets["documents"],
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path = OUTPUT_DIR / "validation_failures.csv"

    failures.to_csv(
        output_path,
        index=False,
    )

    print(f"\nValidation complete.")
    print(f"Total failures: {len(failures)}")
    print(f"Saved to: {output_path}")
    
    
if __name__ == "__main__":
    main()