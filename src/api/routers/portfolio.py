from pathlib import Path

import pandas as pd
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/v1", tags=["Portfolio"])

ROOT = Path(__file__).resolve().parents[3]
STATS_FILE = ROOT / "output" / "portfolio_stats.csv"


@router.get("/portfolio/stats")
def get_portfolio_statistics():
    """Return Day 37 portfolio KPI statistics."""

    if not STATS_FILE.exists():
        raise HTTPException(
            status_code=404,
            detail="Portfolio statistics file not found. Run Day 37 analytics first.",
        )

    try:
        df = pd.read_csv(STATS_FILE)

        records = df.astype(object).where(pd.notna(df), None).to_dict(orient="records")

        return {
            "metric_count": len(records),
            "statistics": records,
        }

    except Exception as error:  # noqa: BLE001
        raise HTTPException(
            status_code=500,
            detail=f"Portfolio statistics failed: {error!s}",
        )
