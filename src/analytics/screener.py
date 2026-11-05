
"""Sprint 3: Financial screener with six preset filters."""

from pathlib import Path
import sqlite3
import pandas as pd


PRESETS = {
    "quality": {
        "return_on_equity_pct": (">=", 15),
        "return_on_capital_employed_pct": (">=", 15),
        "net_profit_margin_pct": (">=", 10),
    },
    "low_debt": {
        "debt_to_equity": ("<=", 0.5),
        "interest_coverage": (">=", 3),
    },
    "cash_generators": {
        "free_cash_flow_cr": (">", 0),
        "cfo_quality_score": (">=", 1),
    },
    "high_returns": {
        "return_on_equity_pct": (">=", 20),
        "return_on_capital_employed_pct": (">=", 20),
    },
    "efficient": {
        "asset_turnover": (">=", 0.75),
        "operating_profit_margin_pct": (">=", 15),
    },
    "balanced": {
        "net_profit_margin_pct": (">=", 10),
        "return_on_equity_pct": (">=", 12),
        "debt_to_equity": ("<=", 1),
        "free_cash_flow_cr": (">", 0),
    },
}


def get_screener_results(db_path, preset="quality"):
    """Return companies matching a preset using latest available records."""

    if preset not in PRESETS:
        raise ValueError(
            f"Unknown preset: {preset}. Choose from {list(PRESETS)}"
        )

    query = """
        WITH latest AS (
            SELECT *,
                   ROW_NUMBER() OVER (
                       PARTITION BY company_id
                       ORDER BY year DESC
                   ) AS rn
            FROM financial_ratios
        )
        SELECT
            f.company_id,
            c.company_name,
            s.broad_sector,
            f.year,
            f.net_profit_margin_pct,
            f.operating_profit_margin_pct,
            f.return_on_equity_pct,
            f.return_on_capital_employed_pct,
            f.debt_to_equity,
            f.interest_coverage,
            f.asset_turnover,
            f.free_cash_flow_cr,
            f.cfo_quality_score,
            f.fcf_conversion_pct
        FROM latest f
        LEFT JOIN companies c ON c.id = f.company_id
        LEFT JOIN sectors s ON s.company_id = f.company_id
        WHERE f.rn = 1
    """

    with sqlite3.connect(db_path) as conn:
        df = pd.read_sql_query(query, conn)

    for column, (operator, threshold) in PRESETS[preset].items():
        if operator == ">=":
            df = df[df[column] >= threshold]
        elif operator == "<=":
            df = df[df[column] <= threshold]
        elif operator == ">":
            df = df[df[column] > threshold]
        elif operator == "<":
            df = df[df[column] < threshold]

    return df.sort_values(
        "return_on_equity_pct", ascending=False
    ).reset_index(drop=True)
