import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "data" / "nifty100.db"


def get_connection():
    """Create a SQLite database connection."""
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Database not found: {DB_PATH}")

    connection = sqlite3.connect(
        str(DB_PATH),
        check_same_thread=False,
        timeout=30,
    )

    connection.row_factory = sqlite3.Row
    return connection


def get_table_row_counts():
    """Return row counts for all user tables."""
    counts = {}

    with get_connection() as connection:
        tables = connection.execute("""
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
            AND name NOT LIKE 'sqlite_%'
            ORDER BY name
            """).fetchall()

        for table in tables:
            table_name = table["name"]

            # Table names originate from SQLite metadata.
            quoted_name = '"' + table_name.replace('"', '""') + '"'

            count = connection.execute(
                f"SELECT COUNT(*) FROM {quoted_name}"
            ).fetchone()[0]

            counts[table_name] = count

    return counts
