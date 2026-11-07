
from fastapi import APIRouter, HTTPException, Query

from src.api.database import get_connection

router = APIRouter(prefix="/api/v1", tags=["Documents"])


@router.get("/companies/{ticker}/documents")
def get_company_documents(
    ticker: str,
    year: int | None = Query(default=None, ge=2000, le=2100),
):
    """Return annual-report document links for a company."""

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

        query = """
            SELECT
                id,
                company_id,
                Year AS year,
                Annual_Report AS annual_report
            FROM documents
            WHERE UPPER(company_id) = UPPER(?)
        """

        params = [ticker]

        if year is not None:
            query += " AND Year = ?"
            params.append(year)

        query += " ORDER BY Year DESC"

        rows = conn.execute(
            query,
            tuple(params),
        ).fetchall()

    return {
        "company_id": company["id"],
        "company_name": company["company_name"],
        "document_count": len(rows),
        "documents": [dict(row) for row in rows],
    }
