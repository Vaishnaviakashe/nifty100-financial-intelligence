"""Check cleaned annual financial data."""

import sqlite3
from pathlib import Path

DB_PATH = Path("data/nifty100.db")


def main() -> None:
    """Check critical cleaning conditions."""

    connection = sqlite3.connect(DB_PATH)

    checks = {
        "P&L duplicate company-year": """
            SELECT COUNT(*)
            FROM (
                SELECT company_id, year
                FROM profitandloss
                GROUP BY company_id, year
                HAVING COUNT(*) > 1
            )
        """,
        "BS duplicate company-year": """
            SELECT COUNT(*)
            FROM (
                SELECT company_id, year
                FROM balancesheet
                GROUP BY company_id, year
                HAVING COUNT(*) > 1
            )
        """,
        "CF duplicate company-year": """
            SELECT COUNT(*)
            FROM (
                SELECT company_id, year
                FROM cashflow
                GROUP BY company_id, year
                HAVING COUNT(*) > 1
            )
        """,
        "P&L PARSE_ERROR years": """
            SELECT COUNT(*)
            FROM profitandloss
            WHERE year = 'PARSE_ERROR' OR year IS NULL
        """,
        "P&L orphan companies": """
            SELECT COUNT(*)
            FROM profitandloss p
            LEFT JOIN companies c
                ON p.company_id = c.id
            WHERE c.id IS NULL
        """,
    }

    for name, query in checks.items():
        result = connection.execute(query).fetchone()[0]
        print(f"{name}: {result}")

    connection.close()


if __name__ == "__main__":
    main()
