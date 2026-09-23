"""Check the SQLite database structure and row counts."""

import sqlite3
from pathlib import Path

DB_PATH = Path("data/nifty100.db")


def main() -> None:
    """Print database tables and row counts."""

    connection = sqlite3.connect(DB_PATH)

    tables = connection.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        ORDER BY name
        """
    ).fetchall()

    print(f"Tables: {len(tables)}")

    for (table_name,) in tables:
        count = connection.execute(
            f"SELECT COUNT(*) FROM {table_name}"
        ).fetchone()[0]

        print(f"{table_name:<20} {count:>6} rows")

    connection.close()


if __name__ == "__main__":
    main()