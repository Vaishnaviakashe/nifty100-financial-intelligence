"""Load all project datasets into the SQLite database."""

from pathlib import Path
import sqlite3

import pandas as pd

from src.etl.loader import load_excel
from src.etl.normaliser import deduplicate_annual_data

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"
DB_PATH = BASE_DIR / "data" / "nifty100.db"
AUDIT_PATH = BASE_DIR / "data" / "processed" / "load_audit.csv"

DATASETS = {
    "companies": ("companies.xlsx", True),
    "profitandloss": ("profitandloss.xlsx", True),
    "balancesheet": ("balancesheet.xlsx", True),
    "cashflow": ("cashflow.xlsx", True),
    "analysis": ("analysis.xlsx", True),
    "documents": ("documents.xlsx", True),
    "prosandcons": ("prosandcons.xlsx", True),
    "sectors": ("sectors.xlsx", False),
    "stock_prices": ("stock_prices.xlsx", False),
    "market_cap": ("market_cap.xlsx", False),
    "financial_ratios": ("financial_ratios.xlsx", False),
    "peer_groups": ("peer_groups.xlsx", False),

}


def prepare_dataframe(
    dataframe: pd.DataFrame,
    table_name: str,
    valid_company_ids: set[str],
) -> tuple[pd.DataFrame, dict[str, int]]:
    """Prepare a DataFrame for insertion into SQLite."""

    original_rows = len(dataframe)
    duplicate_rows_removed = 0
    invalid_year_rows_removed = 0
    orphan_rows_removed = 0

    annual_tables = {
        "profitandloss",
        "balancesheet",
        "cashflow",
        "financial_ratios",
    }

    if table_name in annual_tables:
        before = len(dataframe)

        dataframe = deduplicate_annual_data(dataframe)

        duplicate_rows_removed = before - len(dataframe)

        before = len(dataframe)

        dataframe = dataframe[
            dataframe["year"] != "PARSE_ERROR"
        ].copy()

        invalid_year_rows_removed = before - len(dataframe)

    if "company_id" in dataframe.columns:
        before = len(dataframe)

        dataframe = dataframe[
            dataframe["company_id"].isin(valid_company_ids)
        ].copy()

        orphan_rows_removed = before - len(dataframe)

    if table_name in {"sectors", "stock_prices", "market_cap"}:
        dataframe = dataframe.drop(
            columns=["id"],
            errors="ignore",
        )

    audit = {
        "source_rows": original_rows,
        "rows_loaded": len(dataframe),
        "duplicate_rows_removed": duplicate_rows_removed,
        "invalid_year_rows_removed": invalid_year_rows_removed,
        "orphan_rows_removed": orphan_rows_removed,
    }

    return dataframe, audit

def main() -> None:
    """Load all datasets into SQLite."""

    connection = sqlite3.connect(DB_PATH)
    connection.execute("PRAGMA foreign_keys = ON")

    companies = load_excel(
        RAW_DIR / "companies.xlsx",
        core=True,
    )

    valid_company_ids = set(companies["id"].dropna())
    audit_records = []

    for table_name, (filename, is_core) in DATASETS.items():
        path = RAW_DIR / filename

        print(f"Loading {filename} → {table_name}")

        dataframe = load_excel(path, core=is_core)

        dataframe, audit = prepare_dataframe(
                            dataframe,
                            table_name,
                            valid_company_ids,
                        )

        dataframe.to_sql(
            table_name,
            connection,
            if_exists="append",
            index=False,
        )

        print(f"  Rows loaded: {len(dataframe)}")
        audit["table_name"] = table_name
        audit_records.append(audit)

    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)

    audit_dataframe = pd.DataFrame(audit_records)

    audit_dataframe.to_csv(
        AUDIT_PATH,
        index=False,
    )
    
    connection.commit()
    connection.close()

    print("\nDatabase loading complete.")


if __name__ == "__main__":
    main()