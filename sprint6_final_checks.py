import sqlite3

db = sqlite3.connect("data/nifty100.db")
db.row_factory = sqlite3.Row

print("\n=== AC-16: GENERATED PROS & CONS ===")
rows = db.execute("""
    SELECT company_id,
           SUM(CASE WHEN type='pro' THEN 1 ELSE 0 END) AS pros,
           SUM(CASE WHEN type='con' THEN 1 ELSE 0 END) AS cons
    FROM generated_pros_cons
    GROUP BY company_id
""").fetchall()

both = sum(1 for r in rows if r["pros"] > 0 and r["cons"] > 0)
print("Companies covered:", len(rows))
print("Companies with both:", both, "/ 92")
print("Companies missing either:", 92 - both)

print("\n=== AC-02: FINANCIAL HISTORY ===")
for table in ["profitandloss", "balancesheet", "cashflow"]:
    data = db.execute(f"""
        SELECT COUNT(*) AS companies,
               SUM(CASE WHEN years >= 10 THEN 1 ELSE 0 END) AS ten_years
        FROM (
            SELECT company_id, COUNT(DISTINCT year) AS years
            FROM {table}
            GROUP BY company_id
        )
    """).fetchone()
    print(table, dict(data))

print("\n=== DATABASE COUNTS ===")
for table in ["companies", "financial_ratios", "generated_pros_cons"]:
    print(table, db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])

print("\n=== FOREIGN KEY CHECK ===")
print(db.execute("PRAGMA foreign_key_check").fetchall())

db.close()

print("\n=== API SMOKE TEST ===")
from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)

for path in [
    "/api/v1/health",
    "/api/v1/companies/TCS/ratios",
    "/api/v1/companies/TCS/pros-cons",
]:
    response = client.get(path)
    print(path, "HTTP", response.status_code)

    if "TCS/ratios" in path and response.status_code == 200:
        result = response.json()
        print("TCS ratios response keys:", list(result.keys()))
        print("TCS ratio records:", result.get("record_count", "inspect response"))
