"""Sprint 3: Peer comparison and percentile ranking engine."""

import sqlite3

import pandas as pd

METRICS = {
    "net_profit_margin_pct": True,
    "operating_profit_margin_pct": True,
    "return_on_equity_pct": True,
    "return_on_capital_employed_pct": True,
    "debt_to_equity": False,
    "interest_coverage": True,
    "asset_turnover": True,
    "free_cash_flow_cr": True,
    "cfo_quality_score": True,
    "fcf_conversion_pct": True,
}


def get_peer_rankings(db_path):
    """Calculate metric percentiles within each peer group."""

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
            pg.peer_group_name,
            pg.company_id,
            pg.is_benchmark,
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
        FROM peer_groups pg
        INNER JOIN latest f
            ON f.company_id = pg.company_id
            AND f.rn = 1
        ORDER BY pg.peer_group_name, pg.is_benchmark DESC
    """

    with sqlite3.connect(db_path) as conn:
        df = pd.read_sql_query(query, conn)

    for metric, higher_is_better in METRICS.items():
        df[f"{metric}_percentile"] = (
            df.groupby("peer_group_name")[metric].rank(
                method="average", ascending=higher_is_better, pct=True
            )
            * 100
        )

    percentile_columns = [f"{metric}_percentile" for metric in METRICS]

    df["overall_percentile"] = df[percentile_columns].mean(axis=1)

    df["overall_rank"] = df.groupby("peer_group_name")["overall_percentile"].rank(
        method="min", ascending=False
    )

    return df.sort_values(["peer_group_name", "overall_rank"]).reset_index(drop=True)
