"""Run final data-quality checks against the cleaned SQLite database."""

import sqlite3
from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "nifty100.db"
OUTPUT_PATH = BASE_DIR / "data" / "processed" / "final_validation_failures.csv"


def load_table(
    connection: sqlite3.Connection,
    table_name: str,
) -> pd.DataFrame:
    """Load a SQLite table into a DataFrame."""

    return pd.read_sql_query(
        f"SELECT * FROM {table_name}",
        connection,
    )


def validate_duplicate_years(
    dataframe: pd.DataFrame,
    table_name: str,
) -> pd.DataFrame:
    """Check duplicate company-year combinations."""

    duplicates = dataframe[
        dataframe.duplicated(
            subset=["company_id", "year"],
            keep=False,
        )
    ].copy()

    if duplicates.empty:
        return pd.DataFrame()

    duplicates["field"] = "company_id,year"
    duplicates["issue"] = (
        f"Duplicate company-year in {table_name}"
    )
    duplicates["severity"] = "CRITICAL"
    duplicates["rule_id"] = "DQ-02"

    return duplicates[
        ["company_id", "year", "field", "issue", "severity", "rule_id"]
    ]


def validate_year_format(
    dataframe: pd.DataFrame,
    table_name: str,
) -> pd.DataFrame:
    """Check that all years use YYYY-MM format."""

    valid = dataframe["year"].astype(str).str.fullmatch(
        r"\d{4}-\d{2}"
    )

    failures = dataframe[~valid].copy()

    if failures.empty:
        return pd.DataFrame()

    failures["field"] = "year"
    failures["issue"] = (
        f"Invalid year format in {table_name}"
    )
    failures["severity"] = "CRITICAL"
    failures["rule_id"] = "DQ-07"

    return failures[
        ["company_id", "year", "field", "issue", "severity", "rule_id"]
    ]
    
    
def validate_opm(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Check reported OPM against calculated OPM."""

    valid = (
        dataframe["sales"].notna()
        & dataframe["operating_profit"].notna()
        & dataframe["sales"].ne(0)
        & dataframe["opm_percentage"].notna()
    )

    checked = dataframe[valid].copy()

    calculated_opm = (
        checked["operating_profit"]
        / checked["sales"]
        * 100
    )

    difference = (
        checked["opm_percentage"]
        - calculated_opm
    ).abs()

    failures = checked[difference >= 1.0].copy()

    if failures.empty:
        return pd.DataFrame()

    failures["field"] = "opm_percentage"
    failures["issue"] = (
        "Reported OPM differs from calculated OPM by 1 percentage point or more"
    )
    failures["severity"] = "WARNING"
    failures["rule_id"] = "DQ-05"

    return failures[
        ["company_id", "year", "field", "issue", "severity", "rule_id"]
    ]
    

def validate_positive_sales(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Check for non-positive sales values."""

    failures = dataframe[
        dataframe["sales"].notna()
        & (dataframe["sales"] <= 0)
    ].copy()

    if failures.empty:
        return pd.DataFrame()

    failures["field"] = "sales"
    failures["issue"] = "Sales are zero or negative"
    failures["severity"] = "WARNING"
    failures["rule_id"] = "DQ-06"

    return failures[
        ["company_id", "year", "field", "issue", "severity", "rule_id"]
    ]
    
    
def validate_net_cash(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Check net cash flow against operating, investing, and financing activities."""

    calculated = (
        dataframe["operating_activity"]
        + dataframe["investing_activity"]
        + dataframe["financing_activity"]
    )

    difference = (
        dataframe["net_cash_flow"] - calculated
    ).abs()

    failures = dataframe[
        difference > 10
    ].copy()

    if failures.empty:
        return pd.DataFrame()

    failures["field"] = "net_cash_flow"
    failures["issue"] = (
        "Net cash flow differs from activity total by more than 10 Cr"
    )
    failures["severity"] = "WARNING"
    failures["rule_id"] = "DQ-09"

    return failures[
        ["company_id", "year", "field", "issue", "severity", "rule_id"]
    ]
    
    
    

def validate_balance_sheet(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """Check whether balance-sheet assets and liabilities are within 1%."""

    ratio = (
        (dataframe["total_assets"] - dataframe["total_liabilities"])
        .abs()
        / dataframe["total_assets"].abs()
    )

    failures = dataframe[
        ratio >= 0.01
    ].copy()

    if failures.empty:
        return pd.DataFrame()

    failures["field"] = "total_assets,total_liabilities"
    failures["issue"] = (
        "Total assets and total liabilities differ by 1% or more"
    )
    failures["severity"] = "WARNING"
    failures["rule_id"] = "DQ-04"

    return failures[
        ["company_id", "year", "field", "issue", "severity", "rule_id"]
    ]

def validate_foreign_keys(
    connection: sqlite3.Connection,
    table_name: str,
) -> pd.DataFrame:
    """Check child-table company IDs against companies."""

    query = f"""
        SELECT child.company_id
        FROM {table_name} AS child
        LEFT JOIN companies AS parent
            ON child.company_id = parent.id
        WHERE parent.id IS NULL
    """

    failures = pd.read_sql_query(query, connection)

    if failures.empty:
        return pd.DataFrame()

    failures["field"] = "company_id"
    failures["issue"] = (
        f"Company ID not found in companies table: {table_name}"
    )
    failures["severity"] = "CRITICAL"
    failures["rule_id"] = "DQ-03"

    failures["year"] = pd.NA

    return failures[
        ["company_id", "year", "field", "issue", "severity", "rule_id"]
    ]


def validate_company_pk(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Check that company IDs are unique."""

    duplicates = dataframe[
        dataframe["id"].duplicated(keep=False)
    ].copy()

    if duplicates.empty:
        return pd.DataFrame()

    duplicates["field"] = "id"
    duplicates["issue"] = "Duplicate company ID"
    duplicates["severity"] = "CRITICAL"
    duplicates["rule_id"] = "DQ-01"

    return duplicates[
        ["id", "field", "issue", "severity", "rule_id"]
    ].rename(columns={"id": "company_id"})
    

def validate_ticker_format(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Check that company IDs are valid normalized tickers."""

    invalid = dataframe[
        dataframe["id"].isna()
        | (dataframe["id"].str.len() < 2)
        | (dataframe["id"].str.len() > 12)
        | (dataframe["id"] != dataframe["id"].str.upper())
        | (dataframe["id"] != dataframe["id"].str.strip())
    ].copy()

    if invalid.empty:
        return pd.DataFrame()

    invalid["field"] = "id"
    invalid["issue"] = "Invalid ticker format"
    invalid["severity"] = "CRITICAL"
    invalid["rule_id"] = "DQ-08"

    return invalid[
        ["id", "field", "issue", "severity", "rule_id"]
    ].rename(columns={"id": "company_id"})
    

def validate_fixed_assets(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Check that fixed assets are non-negative."""

    failures = dataframe[
        dataframe["fixed_assets"] < 0
    ].copy()

    if failures.empty:
        return pd.DataFrame()

    failures["field"] = "fixed_assets"
    failures["issue"] = "Fixed assets are negative"
    failures["severity"] = "WARNING"
    failures["rule_id"] = "DQ-10"

    return failures[
        ["company_id", "year", "field", "issue", "severity", "rule_id"]
    ]
    
def validate_tax_rate(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Check that tax percentage is between 0 and 60."""

    failures = dataframe[
        (dataframe["tax_percentage"] < 0)
        | (dataframe["tax_percentage"] > 60)
    ].copy()

    if failures.empty:
        return pd.DataFrame()

    failures["field"] = "tax_percentage"
    failures["issue"] = "Tax percentage outside 0-60 range"
    failures["severity"] = "WARNING"
    failures["rule_id"] = "DQ-11"

    return failures[
        ["company_id", "year", "field", "issue", "severity", "rule_id"]
    ]
    

def validate_dividend_payout(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Check that dividend payout does not exceed 200 percent."""

    failures = dataframe[
        dataframe["dividend_payout"] > 200
    ].copy()

    if failures.empty:
        return pd.DataFrame()

    failures["field"] = "dividend_payout"
    failures["issue"] = "Dividend payout exceeds 200 percent"
    failures["severity"] = "WARNING"
    failures["rule_id"] = "DQ-12"

    return failures[
        ["company_id", "year", "field", "issue", "severity", "rule_id"]
    ]
    

def validate_eps_sign(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Check EPS sign consistency with net profit."""

    failures = dataframe[
        (dataframe["net_profit"] > 0)
        & (dataframe["eps"] <= 0)
    ].copy()

    if failures.empty:
        return pd.DataFrame()

    failures["field"] = "eps"
    failures["issue"] = "EPS is non-positive while net profit is positive"
    failures["severity"] = "WARNING"
    failures["rule_id"] = "DQ-14"

    return failures[
        ["company_id", "year", "field", "issue", "severity", "rule_id"]
    ]
    

def validate_strict_balance(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Check strict equality between total assets and total liabilities."""

    failures = dataframe[
        dataframe["total_assets"] != dataframe["total_liabilities"]
    ].copy()

    if failures.empty:
        return pd.DataFrame()

    failures["field"] = "total_assets"
    failures["issue"] = (
        "Total assets and total liabilities are not exactly equal"
    )
    failures["severity"] = "INFO"
    failures["rule_id"] = "DQ-15"

    return failures[
        ["company_id", "year", "field", "issue", "severity", "rule_id"]
    ]
    


def validate_coverage(dataframe: pd.DataFrame, table_name: str) -> pd.DataFrame:
    """Check that each company has at least five years of data."""

    coverage = (
        dataframe.groupby("company_id")["year"]
        .nunique()
        .reset_index(name="year_count")
    )

    failures = coverage[
        coverage["year_count"] < 5
    ].copy()

    if failures.empty:
        return pd.DataFrame()

    failures["field"] = "year"
    failures["issue"] = (
        f"Less than 5 years of data in {table_name}"
    )
    failures["severity"] = "WARNING"
    failures["rule_id"] = "DQ-16"

    return failures[
        ["company_id", "field", "issue", "severity", "rule_id"]
    ]
    
    
    
def main() -> None:
    """Run final critical data-quality checks."""

    connection = sqlite3.connect(DB_PATH)

    failures = []

    annual_tables = [
        "profitandloss",
        "balancesheet",
        "cashflow",
    ]
    
    companies = load_table(connection, "companies")

    failures.append(
    validate_company_pk(companies)
    )
    
    failures.append(
    validate_ticker_format(companies)
    )
    
    


    for table_name in annual_tables:
        
        dataframe = load_table(connection, table_name)

        failures.append(validate_duplicate_years(dataframe, table_name))
        failures.append(validate_year_format(dataframe, table_name))
        failures.append(validate_coverage(dataframe, table_name))

        if table_name == "balancesheet":
            failures.append(validate_balance_sheet(dataframe))
            failures.append(validate_fixed_assets(dataframe))
            failures.append(validate_strict_balance(dataframe))

        if table_name == "profitandloss":
            failures.append(validate_opm(dataframe))
            failures.append(validate_positive_sales(dataframe))
            failures.append(validate_tax_rate(dataframe))
            failures.append(validate_dividend_payout(dataframe))
            failures.append(validate_eps_sign(dataframe))

        if table_name == "cashflow":
            failures.append(validate_net_cash(dataframe))


    
    child_tables = [
        "profitandloss",
        "balancesheet",
        "cashflow",
        "analysis",
        "documents",
        "prosandcons",
        "sectors",
        "stock_prices",
        "market_cap",
    ]

    for table_name in child_tables:
        failures.append(
            validate_foreign_keys(
                connection,
                table_name,
            )
        )

    connection.close()

    non_empty = [
        dataframe
        for dataframe in failures
        if not dataframe.empty
    ]

    if non_empty:
        result = pd.concat(
            non_empty,
            ignore_index=True,
        )
    else:
        result = pd.DataFrame(
            columns=[
                "company_id",
                "year",
                "field",
                "issue",
                "severity",
                "rule_id",
            ]
        )

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    result.to_csv(
        OUTPUT_PATH,
        index=False,
    )

    print("Final validation complete.")

    critical_count = len(
        result[result["severity"] == "CRITICAL"]
    )

    warning_count = len(
        result[result["severity"] == "WARNING"]
    )

    info_count = len(
        result[result["severity"] == "INFO"]
    )

    print(f"Critical failures: {critical_count}")
    print(f"Warnings: {warning_count}")
    print(f"Info findings: {info_count}")
    print(f"Total findings: {len(result)}")
    print(f"Saved to: {OUTPUT_PATH}")

    if critical_count == 0:
        print("STATUS: PASS")
    else:
        print("STATUS: REVIEW")

if __name__ == "__main__":
    main()