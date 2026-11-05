import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.analytics.peer_engine import get_peer_rankings

DB_PATH = ROOT / "data" / "nifty100.db"
OUTPUT = ROOT / "output"
OUTPUT.mkdir(exist_ok=True)

df = get_peer_rankings(DB_PATH)

path = OUTPUT / "peer_rankings.csv"
df.to_csv(path, index=False)

print("\nPEER ANALYSIS COMPLETED")
print("Companies:", len(df))
print("Peer groups:", df["peer_group_name"].nunique())
print("Output:", path)

print("\nTOP COMPANY IN EACH PEER GROUP:")
print(
    df[df["overall_rank"] == 1][
        ["peer_group_name", "company_id", "overall_percentile"]
    ].to_string(index=False)
)