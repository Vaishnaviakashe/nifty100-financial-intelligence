import sqlite3
import pandas as pd
from pathlib import Path

db_path = Path("data/nifty100.db")
csv_path = Path("output/pros_cons_generated.csv")

df = pd.read_csv(csv_path)

required = {"company_id", "type", "rule_id", "text", "confidence_pct"}
if not required.issubset(df.columns):
    raise ValueError(f"Missing columns: {required - set(df.columns)}")

if not set(df["type"].dropna()).issubset({"pro", "con"}):
    raise ValueError("Unexpected signal type found")

conn = sqlite3.connect(db_path)

try:
    conn.execute("PRAGMA foreign_keys = ON")

    conn.execute("""
        CREATE TABLE IF NOT EXISTS generated_pros_cons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_id TEXT NOT NULL,
            type TEXT NOT NULL CHECK(type IN ('pro', 'con')),
            rule_id INTEGER NOT NULL,
            text TEXT NOT NULL,
            confidence_pct REAL NOT NULL,
            UNIQUE(company_id, type, rule_id),
            FOREIGN KEY(company_id) REFERENCES companies(id)
        )
    """)

    rows = df[
        ["company_id", "type", "rule_id", "text", "confidence_pct"]
    ].itertuples(index=False, name=None)

    conn.executemany("""
        INSERT OR IGNORE INTO generated_pros_cons
        (company_id, type, rule_id, text, confidence_pct)
        VALUES (?, ?, ?, ?, ?)
    """, rows)

    conn.commit()

    print("SIGNAL SYNCHRONIZATION COMPLETE")
    print("CSV signals:", len(df))
    print("Database signals:", conn.execute(
        "SELECT COUNT(*) FROM generated_pros_cons"
    ).fetchone()[0])
    print("Companies covered:", conn.execute(
        "SELECT COUNT(DISTINCT company_id) FROM generated_pros_cons"
    ).fetchone()[0])
    print("Pros:", conn.execute(
        "SELECT COUNT(*) FROM generated_pros_cons WHERE type='pro'"
    ).fetchone()[0])
    print("Cons:", conn.execute(
        "SELECT COUNT(*) FROM generated_pros_cons WHERE type='con'"
    ).fetchone()[0])
    print("Foreign key errors:", conn.execute(
        "PRAGMA foreign_key_check"
    ).fetchall())

finally:
    conn.close()
