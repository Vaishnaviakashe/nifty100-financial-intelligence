"""Run exploratory SQL queries against the Nifty 100 database."""

import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "nifty100.db"
SQL_PATH = BASE_DIR / "exploratory_queries.sql"


def main() -> None:
    """Run exploratory SQL queries."""

    connection = sqlite3.connect(DB_PATH)
    sql = SQL_PATH.read_text(encoding="utf-8")

    queries = [query.strip() for query in sql.split(";") if query.strip()]

    for number, query in enumerate(queries, start=1):
        cursor = connection.execute(query)
        rows = cursor.fetchall()

        print(f"\n--- Query {number} ---")
        for row in rows[:10]:
            print(row)

        if len(rows) > 10:
            print(f"... {len(rows) - 10} more rows")

    connection.close()


if __name__ == "__main__":
    main()
