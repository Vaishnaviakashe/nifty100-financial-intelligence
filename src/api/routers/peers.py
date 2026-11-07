from pathlib import Path

import pandas as pd
from fastapi import APIRouter, HTTPException

from src.analytics.peer_engine import get_peer_rankings
from src.api.database import get_connection

router = APIRouter(prefix="/api/v1", tags=["Peers"])

ROOT = Path(__file__).resolve().parents[3]
DB_PATH = ROOT / "data" / "nifty100.db"


def load_peer_rankings():
    """Load the existing peer ranking engine results."""

    df = get_peer_rankings(str(DB_PATH))

    return df.astype(object).where(pd.notna(df), None)


@router.get("/peers/{group_name}")
def get_peer_group(group_name: str):
    """Return peer rankings for a particular peer group."""

    df = load_peer_rankings()

    result = df[df["peer_group_name"].str.lower() == group_name.lower()]

    if result.empty:
        raise HTTPException(
            status_code=404,
            detail=f"Peer group '{group_name}' not found",
        )

    return {
        "peer_group": group_name,
        "company_count": len(result),
        "rankings": result.to_dict(orient="records"),
    }


@router.get("/companies/{ticker}/peers/compare")
def compare_company_peers(ticker: str):
    """Compare a company with its assigned peer groups."""

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

        groups = conn.execute(
            """
            SELECT peer_group_name, is_benchmark
            FROM peer_groups
            WHERE UPPER(company_id) = UPPER(?)
            ORDER BY peer_group_name
            """,
            (ticker,),
        ).fetchall()

    if not groups:
        raise HTTPException(
            status_code=404,
            detail=f"No peer groups assigned to '{ticker}'",
        )

    df = load_peer_rankings()

    group_names = [row["peer_group_name"] for row in groups]

    result = df[
        (df["peer_group_name"].isin(group_names))
        & (df["company_id"].str.upper() == ticker.upper())
    ]

    return {
        "company_id": company["id"],
        "company_name": company["company_name"],
        "peer_groups": group_names,
        "comparison_count": len(result),
        "comparisons": result.to_dict(orient="records"),
    }
