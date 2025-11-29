from app.database import supabase
import pandas as pd
import random

# ========================
# Generic fetch-all helper
# ========================
def fetch_all_rows(table_name):
    limit = 1000
    offset = 0
    all_rows = []

    while True:
        res = supabase.table(table_name).select("data").range(offset, offset + limit - 1).execute()
        if not res.data:
            break
        all_rows.extend(res.data)
        offset += limit

    return [r["data"] for r in all_rows]


# ========================
# OCEAN LOADER
# ========================
def load_ocean_from_db(sample_size=1000):
    rows = fetch_all_rows("ocean_data")
    if not rows:
        return None

    # Sampling optimization (faster visualization)
    if len(rows) > sample_size:
        rows = random.sample(rows, sample_size)
    print("LOADED FROM SUPABASE:", len(rows), "rows")
    return pd.DataFrame(rows)


# ========================
# TAXONOMY LOADER
# ========================
def load_taxonomy_from_db():
    rows = fetch_all_rows("taxonomy_data")
    if not rows:
        return None
    print("LOADED FROM SUPABASE:", len(rows), "rows")
    return pd.DataFrame(rows)
