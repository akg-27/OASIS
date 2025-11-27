from app.database import supabase

def save_ocean_dataset(df):
    records = df.to_dict(orient="records")

    for row in records:
        for k, v in row.items():
            if v != v:
                row[k] = None

    supabase.table("ocean_data").insert([{"data": row} for row in records]).execute()

    print(f"📌 Saved {len(records)} ocean rows to Supabase")
