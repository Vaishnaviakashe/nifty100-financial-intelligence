import re
import sqlite3
from pathlib import Path

import pandas as pd

# --------------------------------------------------
# PATHS AND CONFIGURATION
# --------------------------------------------------

ROOT = Path(__file__).resolve().parents[2]

DB_PATH = ROOT / "data" / "nifty100.db"
EXCEL_PATH = ROOT / "data" / "raw" / "analysis.xlsx"
OUTPUT_DIR = ROOT / "output"

PARSED_FILE = OUTPUT_DIR / "analysis_parsed.csv"
FAILURES_FILE = OUTPUT_DIR / "parse_failures.csv"
DIVERGENCE_FILE = OUTPUT_DIR / "cagr_divergence_review.csv"
COVERAGE_FILE = OUTPUT_DIR / "analysis_coverage.csv"

METRIC_COLUMNS = {
    "compounded_sales_growth": "sales_cagr",
    "compounded_profit_growth": "profit_cagr",
    "stock_price_cagr": "stock_price_cagr",
    "roe": "roe",
}

# Supports:
# 10 Years: 21%
# 5 Year: -2.5%
# TTM: 43%
# 1 Year: 16%
# Last Year: 12%
PATTERN = re.compile(
    r"^\s*(?P<period>\d+)\s*Years?\s*:?\s*" r"(?P<value>-?\d+(?:\.\d+)?)\s*%?\s*$",
    re.IGNORECASE,
)

SPECIAL_PATTERN = re.compile(
    r"^\s*(?P<period>TTM|Last\s+Year|1\s+Year)"
    r"\s*:?\s*(?P<value>-?\d+(?:\.\d+)?)\s*%?\s*$",
    re.IGNORECASE,
)


# --------------------------------------------------
# PARSE PERIOD AND PERCENTAGE
# --------------------------------------------------


def parse_value(raw_value):
    if pd.isna(raw_value):
        return None, None, "Empty value"

    text = str(raw_value).strip()

    match = PATTERN.match(text)

    if match:
        return (
            int(match.group("period")),
            float(match.group("value")),
            None,
        )

    match = SPECIAL_PATTERN.match(text)

    if match:
        return 1, float(match.group("value")), None

    return None, None, "Does not match supported period format"


# --------------------------------------------------
# LOAD AND PARSE EXCEL
# --------------------------------------------------


def parse_analysis():
    if not EXCEL_PATH.exists():
        raise FileNotFoundError(f"Excel file not found: {EXCEL_PATH}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Original workbook has a title row followed by column headers.
    df = pd.read_excel(EXCEL_PATH, header=1)

    df.columns = [str(col).strip() for col in df.columns]

    required = ["company_id", *METRIC_COLUMNS.keys()]
    missing = [col for col in required if col not in df.columns]

    if missing:
        raise ValueError(f"Missing Excel columns: {missing}")

    parsed_rows = []
    failures = []

    for _, row in df.iterrows():
        company_id = str(row["company_id"]).strip()

        if not company_id or company_id.lower() == "nan":
            continue

        for source_column, metric_type in METRIC_COLUMNS.items():
            raw_value = row[source_column]

            period, value, error = parse_value(raw_value)

            if error:
                failures.append(
                    {
                        "company_id": company_id,
                        "metric_type": metric_type,
                        "raw_value": raw_value,
                        "reason": error,
                    }
                )
                continue

            parsed_rows.append(
                {
                    "company_id": company_id,
                    "metric_type": metric_type,
                    "period_years": period,
                    "value_pct": value,
                }
            )

    parsed = pd.DataFrame(
        parsed_rows,
        columns=[
            "company_id",
            "metric_type",
            "period_years",
            "value_pct",
        ],
    )

    failure_df = pd.DataFrame(
        failures,
        columns=[
            "company_id",
            "metric_type",
            "raw_value",
            "reason",
        ],
    )

    parsed.to_csv(PARSED_FILE, index=False)
    failure_df.to_csv(FAILURES_FILE, index=False)

    print(f"Parsed records: {len(parsed)}")
    print(f"Failed records: {len(failure_df)}")
    print(f"Companies parsed: {parsed['company_id'].nunique()}")
    print(f"Saved: {PARSED_FILE}")
    print(f"Saved: {FAILURES_FILE}")

    return parsed


# --------------------------------------------------
# CALCULATE HISTORICAL CAGR
# --------------------------------------------------


def calculate_cagr(start_value, end_value, years):
    if (
        pd.isna(start_value)
        or pd.isna(end_value)
        or start_value <= 0
        or end_value <= 0
        or years <= 0
    ):
        return None

    return ((end_value / start_value) ** (1 / years) - 1) * 100


def get_statement_cagr(conn, company_id, metric, period):
    column = "sales" if metric == "sales_cagr" else "net_profit"

    query = f"""
        SELECT year, {column}
        FROM profitandloss
        WHERE company_id = ?
          AND {column} > 0
        ORDER BY year
    """

    df = pd.read_sql_query(query, conn, params=(company_id,))

    if len(df) < 2:
        return None

    df["year_num"] = pd.to_numeric(
        df["year"].astype(str).str[:4],
        errors="coerce",
    )

    df = df.dropna(subset=["year_num"])

    if len(df) < 2:
        return None

    latest = df.iloc[-1]
    target_year = latest["year_num"] - period

    # Select the earliest available observation at or after
    # the target year, provided it is close enough.
    candidates = df[df["year_num"] <= target_year + 1]

    if candidates.empty:
        return None

    start = candidates.iloc[-1]
    actual_years = latest["year_num"] - start["year_num"]

    if actual_years < max(1, period - 1):
        return None

    return calculate_cagr(
        start[column],
        latest[column],
        actual_years,
    )


def get_stock_price_cagr(conn, company_id, period):
    df = pd.read_sql_query(
        """
        SELECT date, adjusted_close
        FROM stock_prices
        WHERE company_id = ?
          AND adjusted_close > 0
        ORDER BY date
        """,
        conn,
        params=(company_id,),
    )

    if len(df) < 2:
        return None

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"])

    if df.empty:
        return None

    latest = df.iloc[-1]
    target_date = latest["date"] - pd.DateOffset(years=period)

    candidates = df[df["date"] <= target_date]

    if candidates.empty:
        return None

    start = candidates.iloc[-1]

    actual_years = (latest["date"] - start["date"]).days / 365.25

    if actual_years < period - 0.1:
        return None

    return calculate_cagr(
        start["adjusted_close"],
        latest["adjusted_close"],
        actual_years,
    )


# --------------------------------------------------
# CROSS-VALIDATE CAGR VALUES
# --------------------------------------------------


def cross_validate(parsed):
    conn = sqlite3.connect(DB_PATH)
    review_rows = []

    try:
        for _, row in parsed.iterrows():
            metric = row["metric_type"]
            period = int(row["period_years"])

            # ROE is not a CAGR. TTM and one-year values
            # are not multi-year CAGR observations.
            if metric == "roe" or period <= 1:
                continue

            company_id = row["company_id"]
            parsed_value = float(row["value_pct"])

            computed_value = None
            source = None

            if metric in ("sales_cagr", "profit_cagr"):
                computed_value = get_statement_cagr(
                    conn,
                    company_id,
                    metric,
                    period,
                )
                source = "profitandloss"

            elif metric == "stock_price_cagr":
                computed_value = get_stock_price_cagr(
                    conn,
                    company_id,
                    period,
                )
                source = "stock_prices"

            if computed_value is None:
                continue

            divergence = abs(parsed_value - computed_value)

            # Difference measured in percentage points.
            review_rows.append(
                {
                    "company_id": company_id,
                    "metric_type": metric,
                    "period_years": period,
                    "parsed_value_pct": parsed_value,
                    "computed_value_pct": round(computed_value, 2),
                    "divergence_pct_points": round(divergence, 2),
                    "source_table": source,
                    "manual_review": divergence > 5,
                }
            )

    finally:
        conn.close()

    review_df = pd.DataFrame(review_rows)

    review_df.to_csv(DIVERGENCE_FILE, index=False)

    flagged = int(review_df["manual_review"].sum()) if not review_df.empty else 0

    print("\nCAGR CROSS-VALIDATION")
    print(f"Comparisons available: {len(review_df)}")
    print(f"Flagged for manual review: {flagged}")
    print(f"Saved: {DIVERGENCE_FILE}")

    return review_df


# --------------------------------------------------
# COMPANY COVERAGE
# --------------------------------------------------


def generate_coverage_report(parsed):
    conn = sqlite3.connect(DB_PATH)

    try:
        companies = pd.read_sql_query(
            "SELECT id FROM companies",
            conn,
        )
    finally:
        conn.close()

    all_ids = set(companies["id"].astype(str).str.strip())
    parsed_ids = set(parsed["company_id"].astype(str).str.strip())

    matched_ids = all_ids & parsed_ids
    missing_ids = sorted(all_ids - parsed_ids)
    unmatched_source_ids = sorted(parsed_ids - all_ids)

    coverage = pd.DataFrame(
        {
            "total_companies": [len(all_ids)],
            "source_companies": [len(parsed_ids)],
            "companies_with_analysis": [len(matched_ids)],
            "companies_missing_analysis": [len(missing_ids)],
            "source_tickers_not_in_master": [", ".join(unmatched_source_ids)],
            "missing_company_ids": [", ".join(missing_ids)],
        }
    )

    coverage.to_csv(COVERAGE_FILE, index=False)

    print("\nCOMPANY COVERAGE")
    print(coverage.to_string(index=False))
    print(f"Saved: {COVERAGE_FILE}")


# --------------------------------------------------
# MAIN
# --------------------------------------------------


def main():
    print("=" * 55)
    print("NIFTY 100 - DAY 29 ANALYSIS TEXT PARSER")
    print("=" * 55)

    parsed = parse_analysis()
    cross_validate(parsed)
    generate_coverage_report(parsed)

    print("\nDay 29 parser execution completed.")


if __name__ == "__main__":
    main()
