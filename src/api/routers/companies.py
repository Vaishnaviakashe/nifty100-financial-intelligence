from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse

from src.api.database import get_connection

router = APIRouter(
    prefix="/api/v1",
    tags=["Companies"],
)

ROOT = Path(__file__).resolve().parents[3]
TEARSHEET_DIR = ROOT / "reports" / "tearsheets"


# ============================================================
# HELPER FUNCTIONS
# ============================================================


def fetch_all(query, params=()):
    """Execute a SELECT query and return rows as dictionaries."""

    with get_connection() as connection:
        rows = connection.execute(query, params).fetchall()

    return [dict(row) for row in rows]


def fetch_one(query, params=()):
    """Execute a SELECT query and return one row."""

    with get_connection() as connection:
        row = connection.execute(query, params).fetchone()

    return dict(row) if row else None


def get_company_or_404(ticker):
    """Check whether a company exists."""

    company = fetch_one(
        """
        SELECT *
        FROM companies
        WHERE UPPER(id) = UPPER(?)
        """,
        (ticker,),
    )

    if not company:
        raise HTTPException(
            status_code=404,
            detail=f"Company '{ticker}' not found",
        )

    return company


def get_financial_history(
    ticker,
    table_name,
    year=None,
):
    """Return financial history for a company."""

    # Only allow known database tables.
    allowed_tables = {
        "profitandloss",
        "balancesheet",
        "cashflow",
        "financial_ratios",
    }

    if table_name not in allowed_tables:
        raise ValueError("Invalid financial table")

    get_company_or_404(ticker)

    query = f"""
        SELECT *
        FROM {table_name}
        WHERE UPPER(company_id) = UPPER(?)
    """

    params = [ticker]

    if year:
        query += " AND year = ?"
        params.append(year)

    query += " ORDER BY year DESC"

    records = fetch_all(query, tuple(params))

    return {
        "company_id": ticker.upper(),
        "table": table_name,
        "record_count": len(records),
        "records": records,
    }


# ============================================================
# 1. GET ALL COMPANIES
# ============================================================


@router.get("/companies")
def get_companies(
    sector: str | None = None,
    market_cap_category: str | None = None,
    search: str | None = None,
    limit: int = Query(default=100, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    """List companies with optional filters and pagination."""

    conditions = []
    params = []

    if sector:
        conditions.append("""
            EXISTS (
                SELECT 1
                FROM sectors s
                WHERE s.company_id = c.id
                AND LOWER(s.broad_sector) = LOWER(?)
            )
            """)
        params.append(sector)

    if market_cap_category:
        conditions.append("""
            EXISTS (
                SELECT 1
                FROM sectors s
                WHERE s.company_id = c.id
                AND LOWER(s.market_cap_category) = LOWER(?)
            )
            """)
        params.append(market_cap_category)

    if search:
        conditions.append("""
            (
                LOWER(c.id) LIKE LOWER(?)
                OR LOWER(c.company_name) LIKE LOWER(?)
            )
            """)

        search_value = f"%{search}%"
        params.extend([search_value, search_value])

    where_clause = ""

    if conditions:
        where_clause = "WHERE " + " AND ".join(conditions)

    count_query = f"""
        SELECT COUNT(*)
        FROM companies c
        {where_clause}
    """

    data_query = f"""
        SELECT
            c.*,
            s.broad_sector,
            s.sub_sector,
            s.market_cap_category,
            s.index_weight_pct
        FROM companies c
        LEFT JOIN sectors s
            ON s.company_id = c.id
        {where_clause}
        ORDER BY c.company_name
        LIMIT ? OFFSET ?
    """

    with get_connection() as connection:

        total = connection.execute(
            count_query,
            tuple(params),
        ).fetchone()[0]

        records = connection.execute(
            data_query,
            tuple(params + [limit, offset]),
        ).fetchall()

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "count": len(records),
        "companies": [dict(row) for row in records],
    }


# ============================================================
# 2. GET COMPANY PROFILE
# ============================================================


@router.get("/companies/{ticker}")
def get_company_profile(ticker: str):
    """Return company details and sector information."""

    company = get_company_or_404(ticker)

    sector = fetch_one(
        """
        SELECT *
        FROM sectors
        WHERE UPPER(company_id) = UPPER(?)
        """,
        (ticker,),
    )

    return {
        "company": company,
        "sector": sector,
    }


# ============================================================
# 3. GET PROFIT AND LOSS HISTORY
# ============================================================


@router.get("/companies/{ticker}/pl")
def get_company_profit_loss(
    ticker: str,
    year: str | None = None,
):
    """Return company Profit and Loss history."""

    return get_financial_history(
        ticker,
        "profitandloss",
        year,
    )


# ============================================================
# 4. GET BALANCE SHEET HISTORY
# ============================================================


@router.get("/companies/{ticker}/bs")
def get_company_balance_sheet(
    ticker: str,
    year: str | None = None,
):
    """Return company Balance Sheet history."""

    return get_financial_history(
        ticker,
        "balancesheet",
        year,
    )


# ============================================================
# 5. GET CASH FLOW HISTORY
# ============================================================


@router.get("/companies/{ticker}/cashflow")
def get_company_cashflow(
    ticker: str,
    year: str | None = None,
):
    """Return company Cash Flow history."""

    return get_financial_history(
        ticker,
        "cashflow",
        year,
    )


# ============================================================
# 6. GET FINANCIAL RATIOS
# ============================================================


@router.get("/companies/{ticker}/ratios")
def get_company_ratios(
    ticker: str,
    year: str | None = None,
):
    """Return company financial ratios."""

    return get_financial_history(
        ticker,
        "financial_ratios",
        year,
    )


# ============================================================
# 7. DOWNLOAD COMPANY TEARSHEET
# ============================================================


@router.get("/companies/{ticker}/tearsheet")
def download_company_tearsheet(ticker: str):
    """Download the company's generated PDF tearsheet."""

    get_company_or_404(ticker)

    if not TEARSHEET_DIR.exists():
        raise HTTPException(
            status_code=404,
            detail="Tearsheet directory not found",
        )

    expected_filename = f"{ticker.upper()}_tearsheet.pdf"

    pdf_path = TEARSHEET_DIR / expected_filename

    if not pdf_path.is_file():
        raise HTTPException(
            status_code=404,
            detail=f"Tearsheet for '{ticker}' not found",
        )

    return FileResponse(
        path=pdf_path,
        media_type="application/pdf",
        filename=pdf_path.name,
    )
