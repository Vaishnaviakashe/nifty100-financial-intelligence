"""Inspect supplementary dataset schemas."""

from pathlib import Path

import pandas as pd

RAW_DIR = Path("data/raw")

FILES = [
    "sectors.xlsx",
    "stock_prices.xlsx",
    "market_cap.xlsx",
]


def main() -> None:
    """Print columns for supplementary datasets."""

    for filename in FILES:
        path = RAW_DIR / filename
        dataframe = pd.read_excel(path)

        print(f"\n{filename}")
        print(f"Rows: {len(dataframe)}")
        print("Columns:")
        for column in dataframe.columns:
            print(f"  - {column}")


if __name__ == "__main__":
    main()
