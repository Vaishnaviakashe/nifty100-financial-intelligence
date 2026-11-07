
from pathlib import Path

import pandas as pd
from fastapi import APIRouter, HTTPException, Query

from src.analytics.screener import PRESETS, get_screener_results

router = APIRouter(prefix="/api/v1", tags=["Screener"])

ROOT = Path(__file__).resolve().parents[3]
DB_PATH = ROOT / "data" / "nifty100.db"


@router.get("/screener")
def run_screener(
    preset: str = Query(default="quality"),
    sector: str | None = None,
    limit: int = Query(default=100, ge=1, le=200),
):
    """Run one of the six predefined financial screening strategies."""

    if preset not in PRESETS:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Unknown screener preset",
                "available_presets": list(PRESETS.keys()),
            },
        )

    try:
        df = get_screener_results(
            db_path=str(DB_PATH),
            preset=preset,
        )

        if sector:
            df = df[
                df["broad_sector"].str.lower() == sector.lower()
            ]

        total = len(df)
        df = df.head(limit)

        # Convert pandas NaN values to JSON-compatible nulls.
        records = (
            df.astype(object)
            .where(pd.notna(df), None)
            .to_dict(orient="records")
        )

        return {
            "preset": preset,
            "sector": sector,
            "total_matches": total,
            "returned": len(records),
            "companies": records,
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Screener execution failed: {str(error)}",
        )
