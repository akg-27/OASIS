from datetime import datetime
from app.database import supabase

def extract_metadata(data, dtype):
    return {
        "type": dtype,
        "columns": list(data.columns) if data is not None else None,
        "records": len(data) if data is not None else None,
        "created_at": datetime.now().isoformat()
    }

def save_metadata(meta: dict):
    supabase.table("dataset_metadata").insert({
        "file_path": meta.get("file_path"),
        "dataset_type": meta.get("type"),
        "metadata": meta
    }).execute()
