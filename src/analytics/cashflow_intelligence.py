
"""Sprint 5 - Cash Flow Intelligence Engine."""

import sqlite3
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.analytics.cashflow_kpis import (
    capex_intensity,
    cfo_quality_score,
    capital_allocation_pattern,
)

DB_PATH = ROOT / "data" / "nifty100.db"
ALLOCATION_PATH = ROOT / "output" / "capital_allocation.csv"
OUTPUT_DIR = ROOT / "output"

OUTPUT_DIR.mkdir(exist_ok=True)


def load_table(conn, table):
    return pd.read_sql_query(f"SELECT * FROM {table}", conn)


def prepare_year(df):
    df = df.copy()
    df["year"] = pd.to_datetime(df["year"], errors="coerce")
    df = df.dropna(subset=["year"])
    return df.sort_values(["company_id", "year"])


def latest_records(df):
    if df.empty:
        return df
    return (
        prepare_year(df)
        .groupby("company_id", as_index=False)
        .tail(1)
        .copy()
    )

def calculate_fcf_cagr(group):
    group = group.sort_values("year").tail(5)
    values = group["free_cash_flow_cr"].dropna()

    if len(values) < 2:
        return np.nan

    start = values.iloc[0]
    end = values.iloc[-1]

    years = (
        group.loc[values.index[-1], "year"]
        - group.loc[values.index[0], "year"]
    ).days / 365.25

    if start <= 0 or end <= 0 or years <= 0:
        return np.nan

    return ((end / start) ** (1 / years) - 1) * 100


def main():
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Database not found: {DB_PATH}")

    with sqlite3.connect(DB_PATH) as conn:
        companies = load_table(conn, "companies")
        sectors = load_table(conn, "sectors")
        cashflow = load_table(conn, "cashflow")
        pnl = load_table(conn, "profitandloss")
        ratios = load_table(conn, "financial_ratios")
        balance = load_table(conn, "balancesheet")

    # Company and sector master
    master = companies[["id"]].rename(columns={"id": "company_id"})

    if "company_name" in companies.columns:
        master["company_name"] = companies["company_name"]

    sector_cols = [
        col for col in ["company_id", "broad_sector", "sub_sector"]
        if col in sectors.columns
    ]
    master = master.merge(
        sectors[sector_cols].drop_duplicates("company_id"),
        on="company_id",
        how="left",
    )

    # Prepare annual source tables
    cashflow = prepare_year(cashflow)
    pnl = prepare_year(pnl)
    ratios = prepare_year(ratios)
    balance = prepare_year(balance)

    # Latest annual records
    latest_cf = latest_records(cashflow)
    latest_pnl = latest_records(pnl)
    latest_ratios = latest_records(ratios)
    latest_balance = latest_records(balance)

    # Latest-year cash flow and profit data
    result = master.merge(
        latest_cf[[
            "company_id", "year", "operating_activity",
            "investing_activity", "financing_activity"
        ]].rename(columns={
            "year": "latest_year",
            "operating_activity": "latest_cfo_cr",
            "investing_activity": "latest_cfi_cr",
            "financing_activity": "latest_cff_cr",
        }),
        on="company_id", how="left",
    )

    result = result.merge(
        latest_pnl[["company_id", "net_profit", "sales"]].rename(
            columns={
                "net_profit": "latest_net_profit_cr",
                "sales": "latest_sales_cr",
            }
        ),
        on="company_id", how="left",
    )

    result = result.merge(
        latest_balance[["company_id", "borrowings"]].rename(
            columns={"borrowings": "latest_borrowings_cr"}
        ),
        on="company_id", how="left",
    )

    ratio_cols = [
        col for col in [
            "company_id", "free_cash_flow_cr", "fcf_conversion_pct"
        ] if col in latest_ratios.columns
    ]

    result = result.merge(
        latest_ratios[ratio_cols].rename(columns={
            "free_cash_flow_cr": "latest_fcf_cr",
            "fcf_conversion_pct": "fcf_conversion_pct",
        }),
        on="company_id", how="left",
    )

    # CFO quality: average CFO / PAT over up to five latest years.
    annual = cashflow.merge(
        pnl[["company_id", "year", "net_profit", "sales"]],
        on=["company_id", "year"],
        how="left",
    )

    annual["cfo_pat_ratio"] = np.where(
        annual["net_profit"] > 0,
        annual["operating_activity"] / annual["net_profit"],
        np.nan,
    )

    quality = (
        annual.sort_values("year")
        .groupby("company_id")
        .tail(5)
        .groupby("company_id")["cfo_pat_ratio"]
        .mean()
        .rename("cfo_quality_score")
        .reset_index()
    )

    result = result.merge(quality, on="company_id", how="left")

    def quality_label(score):
        if pd.isna(score):
            return "Insufficient Data"
        if score > 1:
            return "High Quality"
        if score >= 0.5:
            return "Moderate Quality"
        return "Accrual Risk"

    result["cfo_quality_label"] = (
        result["cfo_quality_score"].apply(quality_label)
    )

    # CapEx intensity proxy: absolute net investing cash flow / sales.
    result["capex_intensity_pct"] = result.apply(
        lambda row: capex_intensity(
            row["latest_cfi_cr"], row["latest_sales_cr"]
        )
        if pd.notna(row["latest_cfi_cr"])
        and pd.notna(row["latest_sales_cr"])
        else np.nan,
        axis=1,
    )

    result["capex_label"] = np.select(
        [
            result["capex_intensity_pct"] >= 20,
            result["capex_intensity_pct"] >= 10,
        ],
        ["High Intensity", "Moderate Intensity"],
        default="Low Intensity",
    )
    result.loc[
        result["capex_intensity_pct"].isna(), "capex_label"
    ] = "Insufficient Data"

    # FCF CAGR using available annual financial-ratio history.
    fcf_history = ratios[
        ["company_id", "year", "free_cash_flow_cr"]
    ].dropna(subset=["free_cash_flow_cr"])

    fcf_cagr = (
        fcf_history.groupby("company_id")
        .apply(calculate_fcf_cagr, include_groups=False)
        .rename("fcf_cagr_5yr")
        .reset_index()
    )

    result = result.merge(fcf_cagr, on="company_id", how="left")

    # Distress and deleveraging flags.
    result["distress_flag"] = (
        (result["latest_cfo_cr"] < 0)
        & (result["latest_cff_cr"] > 0)
    )

    
    previous_debt = (
        balance.sort_values("year")
        .groupby("company_id")
        .tail(2)
        .groupby("company_id")
        .first()[["borrowings"]]
        .rename(columns={"borrowings": "previous_borrowings_cr"})
        .reset_index()
    )


    result = result.merge(
        previous_debt, on="company_id", how="left"
    )

    result["deleveraging_flag"] = (
        (result["latest_cff_cr"] < 0)
        & (
            result["latest_borrowings_cr"]
            < result["previous_borrowings_cr"]
        )
    ).fillna(False)

    # Use the existing Sprint 2 annual capital allocation classifications.
    allocation = pd.read_csv(ALLOCATION_PATH)
    allocation["year"] = pd.to_datetime(
        allocation["year"], errors="coerce"
    )
    allocation = allocation.dropna(subset=["year"])

    latest_allocation = (
        allocation.sort_values("year")
        .groupby("company_id", as_index=False)
        .tail(1)[["company_id", "pattern_label"]]
        .rename(columns={
            "pattern_label": "capital_allocation_label"
        })
    )

    result = result.merge(
        latest_allocation, on="company_id", how="left"
    )

    # Fallback only where no historical allocation pattern exists.
    missing_pattern = result["capital_allocation_label"].isna()

    result.loc[missing_pattern, "capital_allocation_label"] = result[
        missing_pattern
    ].apply(
        lambda row: capital_allocation_pattern(
            row["latest_cfo_cr"] or 0,
            row["latest_cfi_cr"] or 0,
            row["latest_cff_cr"] or 0,
        ),
        axis=1,
    )

    # Distress alert file
    alerts = result.loc[
        result["distress_flag"],
        [
            "company_id", "company_name", "broad_sector",
            "latest_year", "latest_cfo_cr", "latest_cff_cr",
            "latest_net_profit_cr",
        ],
    ].copy()

    alerts.to_csv(
        OUTPUT_DIR / "distress_alerts.csv", index=False
    )

    # Final intelligence output
    
    final_columns = [
        "company_id",
        "company_name",
        "broad_sector",
        "latest_year",
        "latest_cfo_cr",
        "latest_cfi_cr",
        "latest_cff_cr",
        "latest_net_profit_cr",
        "latest_sales_cr",
        "latest_borrowings_cr",
        "latest_fcf_cr",
        "cfo_quality_score",
        "cfo_quality_label",
        "capex_intensity_pct",
        "capex_label",
        "fcf_cagr_5yr",
        "fcf_conversion_pct",
        "distress_flag",
        "deleveraging_flag",
        "capital_allocation_label",
    ]


    final = result[
        [col for col in final_columns if col in result.columns]
    ].copy()

    final.to_excel(
        OUTPUT_DIR / "cashflow_intelligence.xlsx",
        index=False,
    )

    print("\nSPRINT 5 - CASH FLOW INTELLIGENCE")
    print("-" * 45)
    print(f"Companies in master: {len(master)}")
    print(f"Companies in output: {len(final)}")
    print(f"Distress alerts: {len(alerts)}")
    print(
        "CFO quality labels:\n",
        final["cfo_quality_label"].value_counts(dropna=False),
    )
    print(
        "\nCapital allocation labels:\n",
        final["capital_allocation_label"].value_counts(dropna=False),
    )
    print("\nGenerated:")
    print("output/cashflow_intelligence.xlsx")
    print("output/distress_alerts.csv")


if __name__ == "__main__":
    main()
