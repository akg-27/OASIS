# NOT IN USE NOW

from app.database import supabase
import pandas as pd
import random


# ============================
# GENERIC FULL-TABLE FETCHER
# ============================

def fetch_all_rows(table_name, columns="*"):
    limit = 2000
    offset = 0
    all_rows = []

    while True:
        res = (
            supabase.table(table_name)
            .select(columns)
            .range(offset, offset + limit - 1)
            .execute()
        )

        if not res.data:
            break

        all_rows.extend(res.data)
        offset += limit

    return all_rows



# ============================
# OCEAN LOADER
# ============================

def load_ocean_from_db(sample_size=2000):
    rows = fetch_all_rows("ocean_data", "*")
    if not rows:
        return None

    # sample (avoid heavy plots)
    if len(rows) > sample_size:
        rows = random.sample(rows, sample_size)

    return pd.DataFrame(rows)
