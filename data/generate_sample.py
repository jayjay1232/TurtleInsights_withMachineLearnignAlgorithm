"""
Generate a realistic sample FINALTURTLE_DATASET.xlsx for demo / testing.
Run: python data/generate_sample.py
"""
import numpy as np
import pandas as pd
from pathlib import Path

rng = np.random.default_rng(42)

# Nesting seasons concentrated Oct–Mar, some activity other months
years = range(2018, 2024)
records = []
turtle_id = 1

for year in years:
    # Number of nests per year (growing slightly)
    n_nests = rng.integers(35, 55) + (year - 2018) * 3
    for _ in range(n_nests):
        # Prefer peak months
        month_weights = [0.12, 0.08, 0.06, 0.03, 0.02, 0.02, 0.03, 0.04, 0.08, 0.18, 0.20, 0.14]
        month = rng.choice(range(1, 13), p=month_weights)
        day = int(rng.integers(1, 28))
        date = pd.Timestamp(year=year, month=month, day=day)

        # Location distribution (some sites more popular)
        loc_weights = [0.14, 0.08, 0.12, 0.07, 0.09, 0.06, 0.05, 0.07, 0.11, 0.10, 0.05, 0.06]
        l_tag = int(rng.choice(range(12), p=loc_weights))

        eggs = int(rng.normal(95, 22))
        eggs = max(40, min(160, eggs))
        hatch_rate = float(np.clip(rng.normal(0.78, 0.12), 0.35, 0.98))
        hatchlings = int(round(eggs * hatch_rate))
        unhatched = eggs - hatchlings

        records.append({
            "TURTLE_NUM": turtle_id,
            "DATE LAID": date,
            "NO. OF EGGS LAID": eggs,
            "NO. OF HATCHLING RELEASED": hatchlings,
            "UNHATCHED EGGS": unhatched,
            "HATCHING RATE": round(hatch_rate, 3),
            "LOCATION": f"Site-{l_tag}",
            "L_TAGNUM": l_tag,
        })
        turtle_id += 1

df = pd.DataFrame(records).sort_values("DATE LAID").reset_index(drop=True)
out = Path(__file__).parent / "FINALTURTLE_DATASET.xlsx"
df.to_excel(out, index=False)
print(f"Wrote {len(df)} records → {out}")
print(df.head())
print(df.describe())
