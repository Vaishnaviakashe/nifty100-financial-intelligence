"""Excel ingestion utilities for the Nifty 100 ETL pipeline."""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from src.etl.normaliser import normalize_ticker, normalize_year

logger = logging.getLogger(__name__)


CORE_FILES = [
    "companies.xlsx",
    "profitandloss.xlsx",
    "balancesheet.xlsx",
    "cashflow.xlsx",
    "analysis.xlsx",
    "documents.xlsx",
    "prosandcons.xlsx",
]


def load_excel(path: str | Path, core: bool = True) -> pd.DataFrame:
    """Load an Excel file using the project's header convention."""

    file_path = Path(path)

    header = 1 if core else 0

    logger.info(
        "Loading %s with header=%s",
        file_path.name,
        header,
    )

    dataframe = pd.read_excel(file_path, header=header)

    if "company_id" in dataframe.columns:
        dataframe["company_id"] = dataframe["company_id"].apply(normalize_ticker)

    if "year" in dataframe.columns:
        dataframe["year"] = dataframe["year"].apply(normalize_year)

    return dataframe
