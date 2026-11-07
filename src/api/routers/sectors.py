from fastapi import APIRouter, HTTPException

from src.api.database import get_connection

router = APIRouter(prefix="/api/v1", tags=["Sectors"])


@router.get("/sectors")
def get_sectors():
    """Return all sectors with company counts."""

    query = """
        SELECT
            broad_sector,
            COUNT(DISTINCT company_id) AS company_count
        FROM sectors
        GROUP BY broad_sector
        ORDER BY broad_sector
    """

    with get_connection() as conn:
        rows = conn.execute(query).fetchall()

    return {
        "total_sectors": len(rows),
        "sectors": [dict(row) for row in rows],
    }


@router.get("/sectors/{sector}/companies")
def get_sector_companies(sector: str):
    """Return companies belonging to a particular sector."""

    query = """
        SELECT
            c.id AS company_id,
            c.company_name,
            s.broad_sector,
            s.sub_sector,
            s.market_cap_category,
            s.index_weight_pct
        FROM sectors s
        JOIN companies c ON c.id = s.company_id
        WHERE LOWER(s.broad_sector) = LOWER(?)
        ORDER BY c.company_name
    """

    with get_connection() as conn:
        rows = conn.execute(query, (sector,)).fetchall()

    if not rows:
        raise HTTPException(
            status_code=404,
            detail=f"Sector '{sector}' not found or has no companies",
        )

    return {
        "sector": sector,
        "company_count": len(rows),
        "companies": [dict(row) for row in rows],
    }
