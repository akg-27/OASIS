from datetime import datetime
from app.database import supabase

def extract_metadata(df, dtype):
    return {
        "dataset_type": dtype,
        "columns": list(df.columns),
        "records": len(df),
        "created_at": datetime.utcnow().isoformat()
    }

def save_metadata(meta: dict):
    supabase.table("dataset_metadata").insert({
        "version": 1,   # REQUIRED
        "dataset_type": meta["dataset_type"],
        "metadata": meta,
        "created_at": meta["created_at"]
    }).execute()
