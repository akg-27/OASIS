from app.database import supabase

def save_taxonomy_dataset(df):
    records = df.to_dict(orient="records")

    # Fix NaN issues
    for row in records:
        for k, v in row.items():
            if v != v:  # NaN check
                row[k] = None

    supabase.table("taxonomy_data").insert([{"data": row} for row in records]).execute()

    print(f"Saved {len(records)} taxonomy rows to Supabase")
