"""Data quality validation rules for the Nifty 100 ETL pipeline."""

from __future__ import annotations

import pandas as pd
import requests


def validate_company_pk(companies: pd.DataFrame) -> pd.DataFrame:
    """Validate uniqueness of company IDs."""

    duplicates = companies[companies["id"].duplicated(keep=False)].copy()

    if duplicates.empty:
        return pd.DataFrame()

    duplicates["rule_id"] = "DQ-01"
    duplicates["field"] = "id"
    duplicates["issue"] = "Duplicate company ID"
    duplicates["severity"] = "CRITICAL"

    return duplicates


def validate_annual_pk(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Validate uniqueness of company-year combinations."""

    duplicates = dataframe[
        dataframe.duplicated(
            subset=["company_id", "year"],
            keep=False,
        )
    ].copy()

    if duplicates.empty:
        return pd.DataFrame()

    duplicates["rule_id"] = "DQ-02"
    duplicates["field"] = "company_id, year"
    duplicates["issue"] = "Duplicate company-year combination"
    duplicates["severity"] = "CRITICAL"

    return duplicates


def validate_fk(
    dataframe: pd.DataFrame,
    companies: pd.DataFrame,
) -> pd.DataFrame:
    """Validate company IDs against the companies master table."""

    valid_ids = set(companies["id"].dropna())

    orphan_rows = dataframe[~dataframe["company_id"].isin(valid_ids)].copy()

    if orphan_rows.empty:
        return pd.DataFrame()

    orphan_rows["rule_id"] = "DQ-03"
    orphan_rows["field"] = "company_id"
    orphan_rows["issue"] = "Company ID not found in companies table"
    orphan_rows["severity"] = "CRITICAL"

    return orphan_rows


def validate_balance_sheet(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Validate that assets and liabilities are within 1%."""

    ratio = (
        dataframe["total_assets"] - dataframe["total_liabilities"]
    ).abs() / dataframe["total_assets"]

    failures = dataframe[ratio >= 0.01].copy()

    if failures.empty:
        return pd.DataFrame()

    failures["rule_id"] = "DQ-04"
    failures["field"] = "total_assets, total_liabilities"
    failures["issue"] = "Assets and liabilities differ by 1% or more"
    failures["severity"] = "WARNING"

    return failures


def validate_opm(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Cross-check source OPM against calculated OPM."""

    calculated_opm = dataframe["operating_profit"] / dataframe["sales"] * 100

    difference = (dataframe["opm_percentage"] - calculated_opm).abs()

    failures = dataframe[difference >= 1.0].copy()

    if failures.empty:
        return pd.DataFrame()

    failures["rule_id"] = "DQ-05"
    failures["field"] = "opm_percentage"
    failures["issue"] = "Source OPM differs from calculated OPM by 1% or more"
    failures["severity"] = "WARNING"

    return failures


def validate_positive_sales(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """Validate positive sales for the supplied company set."""

    failures = dataframe[dataframe["sales"] <= 0].copy()

    if failures.empty:
        return pd.DataFrame()

    failures["rule_id"] = "DQ-06"
    failures["field"] = "sales"
    failures["issue"] = "Sales must be greater than zero"
    failures["severity"] = "WARNING"

    return failures


def validate_year_format(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Validate normalized year format."""

    valid = dataframe["year"].astype(str).str.fullmatch(r"\d{4}-\d{2}")

    failures = dataframe[~valid].copy()

    if failures.empty:
        return pd.DataFrame()

    failures["rule_id"] = "DQ-07"
    failures["field"] = "year"
    failures["issue"] = "Invalid year format"
    failures["severity"] = "CRITICAL"

    return failures


def validate_ticker_format(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Validate normalized ticker format."""

    ticker = dataframe["company_id"].astype(str)

    valid = ticker.eq(ticker.str.strip().str.upper()) & ticker.str.len().between(2, 12)

    failures = dataframe[~valid].copy()

    if failures.empty:
        return pd.DataFrame()

    failures["rule_id"] = "DQ-08"
    failures["field"] = "company_id"
    failures["issue"] = "Invalid ticker format"
    failures["severity"] = "CRITICAL"

    return failures


def validate_net_cash(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Validate net cash flow against its components."""

    calculated = (
        dataframe["operating_activity"]
        + dataframe["investing_activity"]
        + dataframe["financing_activity"]
    )

    difference = (dataframe["net_cash_flow"] - calculated).abs()

    failures = dataframe[difference > 10].copy()

    if failures.empty:
        return pd.DataFrame()

    failures["rule_id"] = "DQ-09"
    failures["field"] = "net_cash_flow"
    failures["issue"] = (
        "Net cash flow differs from cash flow components by more than 10 Cr"
    )
    failures["severity"] = "WARNING"

    return failures


def validate_fixed_assets(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Validate that fixed assets are non-negative."""

    failures = dataframe[dataframe["fixed_assets"] < 0].copy()

    if failures.empty:
        return pd.DataFrame()

    failures["rule_id"] = "DQ-10"
    failures["field"] = "fixed_assets"
    failures["issue"] = "Fixed assets are negative"
    failures["severity"] = "WARNING"

    return failures


def validate_tax_rate(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Validate tax percentage range."""

    failures = dataframe[
        (dataframe["tax_percentage"] < 0) | (dataframe["tax_percentage"] > 60)
    ].copy()

    if failures.empty:
        return pd.DataFrame()

    failures["rule_id"] = "DQ-11"
    failures["field"] = "tax_percentage"
    failures["issue"] = "Tax percentage outside 0 to 60 range"
    failures["severity"] = "WARNING"

    return failures


def validate_dividend_payout(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Validate dividend payout percentage cap."""

    failures = dataframe[dataframe["dividend_payout"] > 200].copy()

    if failures.empty:
        return pd.DataFrame()

    failures["rule_id"] = "DQ-12"
    failures["field"] = "dividend_payout"
    failures["issue"] = "Dividend payout exceeds 200%"
    failures["severity"] = "WARNING"

    return failures


def validate_annual_report_url(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Validate annual report URLs."""

    failures = []

    for _, row in dataframe.iterrows():
        url = row["Annual_Report"]

        try:
            response = requests.head(
                url,
                timeout=10,
                allow_redirects=True,
            )

            if response.status_code != 200:
                failures.append(row)

        except requests.RequestException:
            failures.append(row)

    if not failures:
        return pd.DataFrame()

    result = pd.DataFrame(failures)

    result["rule_id"] = "DQ-13"
    result["field"] = "Annual_Report"
    result["issue"] = "Annual report URL did not return HTTP 200"
    result["severity"] = "WARNING"

    return result


def validate_eps_sign(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Validate EPS sign against positive net profit."""

    failures = dataframe[(dataframe["net_profit"] > 0) & (dataframe["eps"] <= 0)].copy()

    if failures.empty:
        return pd.DataFrame()

    failures["rule_id"] = "DQ-14"
    failures["field"] = "eps"
    failures["issue"] = "EPS is not positive despite positive net profit"
    failures["severity"] = "WARNING"

    return failures


def validate_balance_equality(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Check strict equality between total assets and liabilities."""

    failures = dataframe[
        dataframe["total_liabilities"] != dataframe["total_assets"]
    ].copy()

    if failures.empty:
        return pd.DataFrame()

    failures["rule_id"] = "DQ-15"
    failures["field"] = "total_assets, total_liabilities"
    failures["issue"] = "Total liabilities do not equal total assets"
    failures["severity"] = "INFO"

    return failures


def validate_coverage(
    pnl: pd.DataFrame,
    balance_sheet: pd.DataFrame,
    cashflow: pd.DataFrame,
) -> pd.DataFrame:
    """Validate that companies have at least five years of records."""

    datasets = {
        "profitandloss": pnl,
        "balancesheet": balance_sheet,
        "cashflow": cashflow,
    }

    failures = []

    for name, dataframe in datasets.items():
        coverage = dataframe.groupby("company_id")["year"].nunique()

        insufficient = coverage[coverage < 5]

        for company_id, year_count in insufficient.items():
            failures.append(
                {
                    "company_id": company_id,
                    "field": name,
                    "issue": (f"Only {year_count} years of records; " "minimum is 5"),
                    "severity": "WARNING",
                    "rule_id": "DQ-16",
                }
            )

    return pd.DataFrame(failures)


def collect_failures(*results: pd.DataFrame) -> pd.DataFrame:
    """Combine validation failures into one DataFrame."""

    non_empty = [result for result in results if not result.empty]

    if not non_empty:
        return pd.DataFrame(
            columns=[
                "company_id",
                "field",
                "issue",
                "severity",
                "rule_id",
            ]
        )

    return pd.concat(
        non_empty,
        ignore_index=True,
    )


def run_all_validations(
    companies: pd.DataFrame,
    profitandloss: pd.DataFrame,
    balancesheet: pd.DataFrame,
    cashflow: pd.DataFrame,
    documents: pd.DataFrame,
) -> pd.DataFrame:
    """Run all applicable data quality rules."""

    results = []

    # DQ-01: Company primary key
    results.append(validate_company_pk(companies))

    # DQ-02: Annual primary key
    results.extend(
        [
            validate_annual_pk(profitandloss),
            validate_annual_pk(balancesheet),
            validate_annual_pk(cashflow),
        ]
    )

    # DQ-03: Foreign key integrity
    results.extend(
        [
            validate_fk(profitandloss, companies),
            validate_fk(balancesheet, companies),
            validate_fk(cashflow, companies),
            validate_fk(documents, companies),
        ]
    )

    # DQ-04: Balance sheet balance
    results.append(validate_balance_sheet(balancesheet))

    # DQ-05: OPM cross-check
    results.append(validate_opm(profitandloss))

    # DQ-06: Positive sales
    results.append(validate_positive_sales(profitandloss))

    # DQ-07: Year format
    results.extend(
        [
            validate_year_format(profitandloss),
            validate_year_format(balancesheet),
            validate_year_format(cashflow),
        ]
    )

    # DQ-08: Ticker format
    results.extend(
        [
            validate_ticker_format(profitandloss),
            validate_ticker_format(balancesheet),
            validate_ticker_format(cashflow),
            validate_ticker_format(documents),
        ]
    )

    # DQ-09: Net cash flow
    results.append(validate_net_cash(cashflow))

    # DQ-10: Fixed assets
    results.append(validate_fixed_assets(balancesheet))

    # DQ-11: Tax rate
    results.append(validate_tax_rate(profitandloss))

    # DQ-12: Dividend payout
    results.append(validate_dividend_payout(profitandloss))

    # DQ-13: Annual report URLs
    results.append(validate_annual_report_url(documents))

    # DQ-14: EPS sign consistency
    results.append(validate_eps_sign(profitandloss))

    # DQ-15: Strict balance equality
    results.append(validate_balance_equality(balancesheet))

    # DQ-16: Coverage
    results.append(
        validate_coverage(
            profitandloss,
            balancesheet,
            cashflow,
        )
    )

    return collect_failures(*results)


def deduplicate_annual_data(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Keep the last row for each valid company-year combination."""

    valid_years = dataframe["year"] != "PARSE_ERROR"

    valid_rows = dataframe[valid_years].drop_duplicates(
        subset=["company_id", "year"],
        keep="last",
    )

    invalid_rows = dataframe[~valid_years]

    return pd.concat(
        [valid_rows, invalid_rows],
        ignore_index=True,
    )


def get_duplicate_rows(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Return all rows involved in valid company-year duplicates."""

    valid_years = dataframe["year"] != "PARSE_ERROR"

    duplicates = dataframe[
        valid_years
        & dataframe.duplicated(
            subset=["company_id", "year"],
            keep=False,
        )
    ].copy()

    return duplicates
