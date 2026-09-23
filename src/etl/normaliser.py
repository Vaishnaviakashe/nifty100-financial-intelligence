"""Normalization utilities for the Nifty 100 ETL pipeline."""

from __future__ import annotations

import re

import pandas as pd


PARSE_ERROR = "PARSE_ERROR"

def normalize_year(value: object) -> str:
    """Normalize financial year labels to YYYY-MM format."""

    if pd.isna(value):
        return PARSE_ERROR

    text = str(value).strip()

    if not text:
        return PARSE_ERROR

    if re.fullmatch(r"\d{4}", text):
        return f"{int(text):04d}-03"

    fy_match = re.fullmatch(
        r"FY\s*(\d{2}|\d{4})",
        text,
        re.IGNORECASE,
    )

    if fy_match:
        year = int(fy_match.group(1))

        if year < 100:
            year += 2000

        return f"{year:04d}-03"
    
    if re.fullmatch(r"\d{4}-\d{2}", text):
        return text

    cleaned = re.sub(r"\s+", " ", text)
    cleaned = re.sub(
        r"^([A-Za-z]+)\s*[- ]\s*(\d{2,4})$",
        r"\1-\2",
        cleaned,
    )

    try:
        parsed = pd.to_datetime(cleaned, format="%b-%y", errors="raise")
        return parsed.strftime("%Y-%m")
    except (ValueError, TypeError):
        try:
            parsed = pd.to_datetime(cleaned, errors="raise")
            return parsed.strftime("%Y-%m")
        except (ValueError, TypeError):
            return PARSE_ERROR
    
    
def normalize_ticker(value: object) -> str:
    """Normalize an NSE ticker by stripping whitespace and uppercasing."""

    if pd.isna(value):
        return PARSE_ERROR

    ticker = str(value).strip().upper()

    if not ticker:
        return PARSE_ERROR

    return ticker


def deduplicate_annual_data(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Keep the last row for each valid company-year combination."""

    valid_years = dataframe["year"] != PARSE_ERROR

    valid_rows = dataframe[valid_years].drop_duplicates(
        subset=["company_id", "year"],
        keep="last",
    )

    invalid_rows = dataframe[~valid_years]

    return pd.concat(
        [valid_rows, invalid_rows],
        ignore_index=True,
    )