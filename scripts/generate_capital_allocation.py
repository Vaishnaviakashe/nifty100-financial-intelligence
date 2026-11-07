import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))


import csv
import sqlite3

from src.analytics.cashflow_kpis import capital_allocation_pattern

DB_PATH = Path("data/nifty100.db")
OUTPUT_PATH = Path("output/capital_allocation.csv")


def sign(value):
    if value > 0:
        return 1
    if value < 0:
        return -1
    return 0


conn = sqlite3.connect(DB_PATH)

query = """
SELECT
    c.company_id,
    c.year,
    c.operating_activity AS cfo,
    c.investing_activity AS cfi,
    c.financing_activity AS cff
FROM cashflow c
WHERE c.company_id IN (
    SELECT id FROM companies
)
ORDER BY c.company_id, c.year
"""

rows = conn.execute(query).fetchall()
conn.close()

output_rows = []

for company_id, year, cfo, cfi, cff in rows:

    cfo = cfo or 0
    cfi = cfi or 0
    cff = cff or 0

    cfo_sign = sign(cfo)
    cfi_sign = sign(cfi)
    cff_sign = sign(cff)

    pattern = capital_allocation_pattern(cfo, cfi, cff)

    output_rows.append(
        {
            "company_id": company_id,
            "year": year,
            "CFO_sign": cfo_sign,
            "CFI_sign": cfi_sign,
            "CFF_sign": cff_sign,
            "pattern_label": pattern,
        }
    )


OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

with open(OUTPUT_PATH, "w", newline="", encoding="utf-8") as f:

    writer = csv.DictWriter(
        f,
        fieldnames=[
            "company_id",
            "year",
            "CFO_sign",
            "CFI_sign",
            "CFF_sign",
            "pattern_label",
        ],
    )

    writer.writeheader()
    writer.writerows(output_rows)


print("=" * 50)
print("D11 CAPITAL ALLOCATION")
print("=" * 50)
print(f"Rows generated : {len(output_rows)}")
print(f"Output         : {OUTPUT_PATH}")
print("=" * 50)
