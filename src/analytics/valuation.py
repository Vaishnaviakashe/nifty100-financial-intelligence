"""NIFTY 100 valuation analytics."""

import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB_PATH = PROJECT_ROOT / "data" / "nifty100.db"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "output"


def read_sql(db_path, sql, params=()):
    if not Path(db_path).exists():
        raise FileNotFoundError(f"Database not found: {db_path}")
    with sqlite3.connect(db_path) as conn:
        return pd.read_sql_query(sql, conn, params=params)


def build_valuation_summary(year=2024, db_path=DEFAULT_DB_PATH):
    companies = read_sql(
        db_path,
        """
        SELECT id AS company_id, TRIM(company_name) AS company_name
        FROM companies ORDER BY company_name
    """,
    )
    sectors = read_sql(
        db_path,
        """
        SELECT company_id, broad_sector AS sector FROM sectors
    """,
    )
    market = read_sql(
        db_path,
        """
        WITH ranked AS (
            SELECT *,
                ROW_NUMBER() OVER (
                    PARTITION BY company_id
                    ORDER BY CAST(SUBSTR(year, 1, 4) AS INTEGER) DESC, year DESC
                ) AS rn
            FROM market_cap
            WHERE CAST(SUBSTR(year, 1, 4) AS INTEGER) <= ?
        )
        SELECT company_id, year AS market_year, market_cap_crore,
               pe_ratio, pb_ratio, ev_ebitda
        FROM ranked WHERE rn = 1
    """,
        (year,),
    )
    ratios = read_sql(
        db_path,
        """
        WITH ranked AS (
            SELECT *,
                ROW_NUMBER() OVER (
                    PARTITION BY company_id
                    ORDER BY CAST(SUBSTR(year, 1, 4) AS INTEGER) DESC, year DESC
                ) AS rn
            FROM financial_ratios
            WHERE CAST(SUBSTR(year, 1, 4) AS INTEGER) <= ?
        )
        SELECT company_id, year AS ratio_year, free_cash_flow_cr
        FROM ranked WHERE rn = 1
    """,
        (year,),
    )
    history = read_sql(
        db_path,
        """
        SELECT company_id, year, pe_ratio
        FROM market_cap
        WHERE CAST(SUBSTR(year, 1, 4) AS INTEGER) <= ?
        ORDER BY company_id, CAST(SUBSTR(year, 1, 4) AS INTEGER), year
    """,
        (year,),
    )

    for frame, cols in [
        (market, ["market_cap_crore", "pe_ratio", "pb_ratio", "ev_ebitda"]),
        (ratios, ["free_cash_flow_cr"]),
        (history, ["pe_ratio"]),
    ]:
        for col in cols:
            frame[col] = pd.to_numeric(frame[col], errors="coerce").replace(
                [np.inf, -np.inf], np.nan
            )

    history = history.dropna(subset=["pe_ratio"]).sort_values(["company_id", "year"])
    five_year = (
        history.groupby("company_id", group_keys=False)
        .tail(5)
        .groupby("company_id")["pe_ratio"]
        .median()
        .rename("5yr_median_PE")
        .reset_index()
    )

    df = (
        companies.merge(sectors, on="company_id", how="left")
        .merge(market, on="company_id", how="left")
        .merge(ratios, on="company_id", how="left")
        .merge(five_year, on="company_id", how="left")
    )

    df["FCF_yield_pct"] = np.where(
        df["market_cap_crore"].gt(0) & df["free_cash_flow_cr"].notna(),
        df["free_cash_flow_cr"] / df["market_cap_crore"] * 100,
        np.nan,
    )

    df["_positive_pe"] = df["pe_ratio"].where(df["pe_ratio"] > 0)
    sector_medians = (
        df.groupby("sector", dropna=True)["_positive_pe"]
        .median()
        .rename("_sector_median_pe")
    )
    df = df.join(sector_medians, on="sector")

    valid = df["_sector_median_pe"].gt(0) & df["pe_ratio"].gt(0)
    df["PE_vs_sector_median_pct"] = np.where(
        valid,
        (df["pe_ratio"] / df["_sector_median_pe"] - 1) * 100,
        np.nan,
    )
    df["valuation_flag"] = np.select(
        [
            ~valid,
            df["pe_ratio"] > df["_sector_median_pe"] * 1.5,
            df["pe_ratio"] < df["_sector_median_pe"] * 0.7,
        ],
        ["Insufficient Data", "Caution", "Discount"],
        default="Fair",
    )

    df = df.rename(
        columns={
            "pe_ratio": "P/E",
            "pb_ratio": "P/B",
            "ev_ebitda": "EV/EBITDA",
        }
    )
    columns = [
        "company_id",
        "company_name",
        "sector",
        "P/E",
        "P/B",
        "EV/EBITDA",
        "FCF_yield_pct",
        "5yr_median_PE",
        "PE_vs_sector_median_pct",
        "valuation_flag",
    ]
    return (
        df[columns]
        .sort_values(["valuation_flag", "company_name"])
        .reset_index(drop=True)
    )


def export_valuation_outputs(
    year=2024, db_path=DEFAULT_DB_PATH, output_dir=DEFAULT_OUTPUT_DIR
):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = build_valuation_summary(year=year, db_path=db_path)

    xlsx_path = output_dir / "valuation_summary.xlsx"
    csv_path = output_dir / "valuation_flags.csv"

    methodology = pd.DataFrame(
        {
            "Metric": [
                "FCF Yield",
                "5Y Median P/E",
                "Sector Median P/E",
                "Discount",
                "Fair",
                "Caution",
            ],
            "Definition": [
                "Latest FCF / latest market capitalisation × 100.",
                "Median of up to five latest annual P/E observations up to selected year.",
                "Median positive latest P/E of companies in the same broad sector.",
                "Company P/E below 70% of sector median.",
                "Company P/E between 70% and 150% of sector median.",
                "Company P/E above 150% of sector median.",
            ],
        }
    )
    with pd.ExcelWriter(xlsx_path, engine="openpyxl") as writer:
        summary.to_excel(writer, sheet_name="Valuation Summary", index=False)
        methodology.to_excel(writer, sheet_name="Methodology", index=False)
        for sheet in writer.book.worksheets:
            sheet.freeze_panes = "A2"
            sheet.auto_filter.ref = sheet.dimensions
            for cells in sheet.columns:
                width = max(len(str(c.value or "")) for c in cells) + 2
                sheet.column_dimensions[cells[0].column_letter].width = min(
                    max(width, 12), 42
                )

    summary[summary["valuation_flag"].isin(["Caution", "Discount"])].to_csv(
        csv_path, index=False
    )
    return summary, xlsx_path, csv_path
