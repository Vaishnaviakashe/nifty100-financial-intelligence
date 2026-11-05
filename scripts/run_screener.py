import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.analytics.screener import PRESETS, get_screener_results

DB_PATH = ROOT / "data" / "nifty100.db"
OUTPUT = ROOT / "output"
OUTPUT.mkdir(exist_ok=True)

for preset in PRESETS:
    df = get_screener_results(DB_PATH, preset)
    path = OUTPUT / f"screener_{preset}.csv"
    df.to_csv(path, index=False)
    print(f"{preset}: {len(df)} companies -> {path.name}")

print("\nSCREENER COMPLETED")