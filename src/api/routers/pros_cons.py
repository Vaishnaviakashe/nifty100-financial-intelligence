from fastapi import APIRouter, HTTPException, Query

from src.api.database import get_connection

router = APIRouter(prefix="/api/v1", tags=["Pros & Cons"])


@router.get("/companies/{ticker}/pros-cons")
def get_company_pros_cons(
    ticker: str,
    signal_type: str | None = Query(
        default=None,
        alias="type",
        description="Filter by pro or con",
    ),
):
    """Return generated pros and cons for a company."""

    if signal_type is not None and signal_type.lower() not in {"pro", "con"}:
        raise HTTPException(
            status_code=400,
            detail="type must be either 'pro' or 'con'",
        )

    with get_connection() as connection:
        company = connection.execute(
            "SELECT id FROM companies WHERE UPPER(id) = UPPER(?)",
            (ticker,),
        ).fetchone()

        if company is None:
            raise HTTPException(
                status_code=404,
                detail=f"Company '{ticker}' not found",
            )

        query = """
            SELECT type, rule_id, text, confidence_pct
            FROM generated_pros_cons
            WHERE UPPER(company_id) = UPPER(?)
        """
        params = [ticker]

        if signal_type:
            query += " AND type = ?"
            params.append(signal_type.lower())

        query += " ORDER BY type, rule_id"

        rows = connection.execute(query, params).fetchall()

    signals = [dict(row) for row in rows]
    pros = [item for item in signals if item["type"] == "pro"]
    cons = [item for item in signals if item["type"] == "con"]

    return {
        "company_id": company["id"],
        "total_signals": len(signals),
        "pros_count": len(pros),
        "cons_count": len(cons),
        "pros": pros,
        "cons": cons,
    }
