
from pathlib import Path

import pandas as pd
from fastapi import APIRouter, HTTPException, Query

from src.analytics.valuation import build_valuation_summary
from src.api.database import get_connection

router = APIRouter(prefix="/api/v1", tags=["Valuation"])

ROOT = Path(__file__).resolve().parents[3]
DB_PATH = ROOT / "data" / "nifty100.db"


@router.get("/market-cap/{ticker}")
def get_market_cap_history(ticker: str):
    """Return historical market capitalization and valuation multiples."""

    with get_connection() as conn:
        company = conn.execute(
            """
            SELECT id, company_name
            FROM companies
            WHERE UPPER(id) = UPPER(?)
            """,
            (ticker,),
        ).fetchone()

        if not company:
            raise HTTPException(
                status_code=404,
                detail=f"Company '{ticker}' not found",
            )

        rows = conn.execute(
            """
            SELECT
                year,
                market_cap_crore,
                enterprise_value_crore,
                pe_ratio,
                pb_ratio,
                ev_ebitda,
                dividend_yield_pct
            FROM market_cap
            WHERE UPPER(company_id) = UPPER(?)
            ORDER BY year
            """,
            (ticker,),
        ).fetchall()

    return {
        "company_id": company["id"],
        "company_name": company["company_name"],
        "record_count": len(rows),
        "history": [dict(row) for row in rows],
    }


@router.get("/valuation/summary")
def get_valuation_summary(
    year: int = Query(default=2024, ge=2019, le=2024),
):
    """Return the existing valuation summary for a selected year."""

    try:
        df = build_valuation_summary(
            year=year,
            db_path=DB_PATH,
        )

        records = (
            df.astype(object)
            .where(pd.notna(df), None)
            .to_dict(orient="records")
        )

        return {
            "year": year,
            "company_count": len(records),
            "valuation_summary": records,
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Valuation summary failed: {str(error)}",
        )
