"""Populate Sprint 2 financial ratios into SQLite."""


import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from pathlib import Path
import sqlite3



from src.analytics.ratios import (
    net_profit_margin,
    operating_profit_margin,
    return_on_equity,
    return_on_capital_employed,
    debt_to_equity,
    interest_coverage,
    asset_turnover,
)

from src.analytics.cashflow_kpis import (
    free_cash_flow,
    capex_intensity,
    fcf_conversion,
    cfo_quality_score,
)


BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "nifty100.db"


def value(x):
    """Convert database NULL to zero for calculations."""
    return 0 if x is None else x


def main():

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row

    # Clear existing Sprint 2 output.
    connection.execute("DELETE FROM financial_ratios")

    rows = connection.execute(
        """
        SELECT
            p.company_id,
            p.year,
            p.sales,
            p.operating_profit,
            p.opm_percentage,
            p.other_income,
            p.interest,
            p.net_profit,
            p.eps,
            p.dividend_payout,

            b.equity_capital,
            b.reserves,
            b.borrowings,
            b.total_assets,

            c.operating_activity,
            c.investing_activity,
            c.financing_activity

        FROM profitandloss p

        LEFT JOIN balancesheet b
            ON p.company_id = b.company_id
            AND p.year = b.year

        LEFT JOIN cashflow c
            ON p.company_id = c.company_id
            AND p.year = c.year

        ORDER BY p.company_id, p.year
        """
    ).fetchall()

    print(f"Source company-year rows: {len(rows)}")

    inserted = 0

    for row in rows:

        sales = value(row["sales"])
        operating_profit = value(row["operating_profit"])
        other_income = value(row["other_income"])
        interest = value(row["interest"])
        net_profit = value(row["net_profit"])

        equity = value(row["equity_capital"])
        reserves = value(row["reserves"])
        borrowings = value(row["borrowings"])
        total_assets = value(row["total_assets"])

        cfo = value(row["operating_activity"])
        cfi = value(row["investing_activity"])

        # --------------------------------------------------
        # PROFITABILITY
        # --------------------------------------------------

        npm = net_profit_margin(
            net_profit,
            sales,
        )

        opm = operating_profit_margin(
            operating_profit,
            sales,
        )

        roe = return_on_equity(
            net_profit,
            equity,
            reserves,
        )

        # EBIT = Operating Profit + Other Income
        ebit = operating_profit + other_income

        roce = return_on_capital_employed(
            ebit,
            equity,
            reserves,
            borrowings,
        )

        # --------------------------------------------------
        # LEVERAGE + EFFICIENCY
        # --------------------------------------------------

        de = debt_to_equity(
            borrowings,
            equity,
            reserves,
        )

        coverage = interest_coverage(
            operating_profit,
            other_income,
            interest,
        )

        turnover = asset_turnover(
            sales,
            total_assets,
        )

        # --------------------------------------------------
        # CASH FLOW
        # --------------------------------------------------

        fcf = free_cash_flow(
            cfo,
            cfi,
        )

        capex = abs(cfi)

        cfo_quality = cfo_quality_score(
            cfo,
            net_profit,
        )

        fcf_conversion_value = fcf_conversion(
            fcf,
            net_profit,
        )

        # --------------------------------------------------
        # INSERT
        # --------------------------------------------------

        connection.execute(
            """
            INSERT INTO financial_ratios (
                company_id,
                year,

                net_profit_margin_pct,
                operating_profit_margin_pct,
                return_on_equity_pct,
                return_on_capital_employed_pct,

                debt_to_equity,
                interest_coverage,
                asset_turnover,

                free_cash_flow_cr,
                capex_cr,
                cfo_quality_score,
                fcf_conversion_pct,

                earnings_per_share,
                book_value_per_share,
                dividend_payout_ratio_pct,
                total_debt_cr,
                cash_from_operations_cr
            )
            VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?, ?, ?
            )
            """,
            (
                row["company_id"],
                row["year"],

                npm,
                opm,
                roe,
                roce,

                de,
                coverage,
                turnover,

                fcf,
                capex,
                cfo_quality,
                fcf_conversion_value,

                row["eps"],
                None,
                row["dividend_payout"],
                borrowings,
                cfo,
            ),
        )

        inserted += 1

    connection.commit()

    final_count = connection.execute(
        "SELECT COUNT(*) FROM financial_ratios"
    ).fetchone()[0]

    companies = connection.execute(
        "SELECT COUNT(DISTINCT company_id) FROM financial_ratios"
    ).fetchone()[0]

    years = connection.execute(
        "SELECT COUNT(DISTINCT year) FROM financial_ratios"
    ).fetchone()[0]

    print()
    print("=" * 50)
    print("SPRINT 2 RATIO ENGINE")
    print("=" * 50)
    print(f"Rows inserted       : {inserted}")
    print(f"Rows in DB          : {final_count}")
    print(f"Companies           : {companies}")
    print(f"Distinct years      : {years}")
    print("=" * 50)

    connection.close()


if __name__ == "__main__":
    main()